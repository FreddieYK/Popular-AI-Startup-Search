from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
import logging
import json

from ..core.database import SessionLocal
from ..core.config import get_settings
from ..models import ScheduledTask, Company
from .data_collection_service import DataCollectionService
from .analysis_service import AnalysisService

logger = logging.getLogger(__name__)
settings = get_settings()

class SchedulerService:
    """任务调度服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.is_running = False
        
    def start_scheduler(self):
        """启动调度器"""
        if self.scheduler is not None:
            logger.warning("调度器已经在运行")
            return
            
        if not settings.enable_scheduler:
            logger.info("调度器已禁用，跳过启动")
            return
        
        self.scheduler = AsyncIOScheduler(timezone=settings.timezone)
        
        # 添加预定义的任务
        self._add_monthly_tasks()
        
        # 启动调度器
        self.scheduler.start()
        self.is_running = True
        
        logger.info("任务调度器启动成功")
    
    def stop_scheduler(self):
        """停止调度器"""
        if self.scheduler is not None:
            self.scheduler.shutdown()
            self.scheduler = None
            self.is_running = False
            logger.info("任务调度器已停止")
    
    def _add_monthly_tasks(self):
        """添加月度任务"""
        # 月度数据采集任务 - 每月1日凌晨2点
        self.scheduler.add_job(
            func=self._monthly_data_collection_job,
            trigger=CronTrigger(day=1, hour=2, minute=0),
            id="monthly_data_collection",
            name="月度数据采集任务",
            replace_existing=True,
            max_instances=1
        )
        
        # 月度同比分析任务 - 每月1日早上6点
        self.scheduler.add_job(
            func=self._monthly_analysis_job,
            trigger=CronTrigger(day=1, hour=6, minute=0),
            id="monthly_analysis",
            name="月度同比分析任务",
            replace_existing=True,
            max_instances=1
        )
        
        # 月度报告生成任务 - 每月1日早上8点
        self.scheduler.add_job(
            func=self._monthly_report_job,
            trigger=CronTrigger(day=1, hour=8, minute=0),
            id="monthly_report",
            name="月度报告生成任务",
            replace_existing=True,
            max_instances=1
        )
        
        logger.info("月度任务已添加到调度器")
    
    async def _monthly_data_collection_job(self):
        """月度数据采集任务"""
        logger.info("开始执行月度数据采集任务")
        
        try:
            # 创建新的数据库会话
            db = SessionLocal()
            collection_service = DataCollectionService(db)
            
            # 采集当前月份数据
            result = await collection_service.collect_current_month_data()
            
            # 记录任务执行结果
            await self._record_task_execution(
                task_type="monthly_data_collection",
                result=result,
                db=db
            )
            
            logger.info(f"月度数据采集任务完成: {result.get('message', '')}")
            
        except Exception as e:
            logger.error(f"月度数据采集任务执行失败: {str(e)}")
            
            # 记录失败结果
            db = SessionLocal()
            await self._record_task_execution(
                task_type="monthly_data_collection",
                result={"success": False, "error": str(e)},
                db=db
            )
        finally:
            if 'db' in locals():
                db.close()
    
    async def _monthly_analysis_job(self):
        """月度同比分析任务"""
        logger.info("开始执行月度同比分析任务")
        
        try:
            # 创建新的数据库会话
            db = SessionLocal()
            analysis_service = AnalysisService(db)
            
            # 执行月度同比分析
            result = analysis_service.calculate_monthly_yoy_analysis()
            
            # 记录任务执行结果
            await self._record_task_execution(
                task_type="monthly_analysis",
                result=result,
                db=db
            )
            
            logger.info(f"月度同比分析任务完成: {result.get('message', '')}")
            
        except Exception as e:
            logger.error(f"月度同比分析任务执行失败: {str(e)}")
            
            # 记录失败结果
            db = SessionLocal()
            await self._record_task_execution(
                task_type="monthly_analysis",
                result={"success": False, "error": str(e)},
                db=db
            )
        finally:
            if 'db' in locals():
                db.close()
    
    async def _monthly_report_job(self):
        """月度报告生成任务"""
        logger.info("开始执行月度报告生成任务")
        
        try:
            # 创建新的数据库会话
            db = SessionLocal()
            
            # 这里可以实现报告生成逻辑
            # 例如：生成CSV文件、发送邮件等
            result = {
                "success": True,
                "message": "月度报告生成完成",
                "generated_at": datetime.now().isoformat()
            }
            
            # 记录任务执行结果
            await self._record_task_execution(
                task_type="monthly_report",
                result=result,
                db=db
            )
            
            logger.info("月度报告生成任务完成")
            
        except Exception as e:
            logger.error(f"月度报告生成任务执行失败: {str(e)}")
            
            # 记录失败结果
            db = SessionLocal()
            await self._record_task_execution(
                task_type="monthly_report",
                result={"success": False, "error": str(e)},
                db=db
            )
        finally:
            if 'db' in locals():
                db.close()
    
    async def _record_task_execution(
        self, 
        task_type: str, 
        result: Dict[str, Any], 
        db: Session
    ):
        """记录任务执行结果"""
        try:
            # 查找或创建任务记录
            task_record = db.query(ScheduledTask).filter(
                ScheduledTask.task_type == task_type
            ).first()
            
            if not task_record:
                task_record = ScheduledTask(
                    task_type=task_type,
                    schedule_pattern="0 2 1 * *" if task_type == "monthly_data_collection" else 
                                   "0 6 1 * *" if task_type == "monthly_analysis" else "0 8 1 * *",
                    status="active"
                )
                db.add(task_record)
            
            # 更新任务记录
            task_record.last_run = datetime.now()
            
            # 计算下次运行时间（简化版本）
            next_month = datetime.now().replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1)
            
            if task_type == "monthly_data_collection":
                task_record.next_run = next_month.replace(hour=2, minute=0, second=0, microsecond=0)
            elif task_type == "monthly_analysis":
                task_record.next_run = next_month.replace(hour=6, minute=0, second=0, microsecond=0)
            else:  # monthly_report
                task_record.next_run = next_month.replace(hour=8, minute=0, second=0, microsecond=0)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"记录任务执行结果失败: {str(e)}")
    
    def get_automation_status(self) -> Dict[str, Any]:
        """获取自动化任务状态"""
        # 获取所有调度任务
        tasks = self.db.query(ScheduledTask).filter(
            ScheduledTask.status == "active"
        ).all()
        
        # 获取下次运行时间和上次运行时间
        next_run = None
        last_run = None
        
        if tasks:
            next_runs = [task.next_run for task in tasks if task.next_run]
            last_runs = [task.last_run for task in tasks if task.last_run]
            
            if next_runs:
                next_run = min(next_runs).isoformat()
            
            if last_runs:
                last_run = max(last_runs).isoformat()
        
        return {
            "enabled": self.is_running and settings.enable_scheduler,
            "scheduler_running": self.is_running,
            "next_run": next_run,
            "last_run": last_run,
            "total_tasks": len(tasks),
            "active_tasks": len([t for t in tasks if t.status == "active"])
        }
    
    def enable_automation(self):
        """启用自动化任务"""
        if not self.is_running:
            self.start_scheduler()
    
    def disable_automation(self):
        """禁用自动化任务"""
        if self.is_running:
            self.stop_scheduler()
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取特定任务状态"""
        if not self.scheduler:
            return None
        
        job = self.scheduler.get_job(job_id)
        if not job:
            return None
        
        return {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        }
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """列出所有任务"""
        if not self.scheduler:
            return []
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return jobs