"""
文件迁移工具：将现有上传文件按日期重新组织
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import UploadedFile

class FileMigrator:
    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = base_dir
        self.migrated_count = 0
        self.error_count = 0
        self.errors = []

    def get_date_path_from_datetime(self, dt: datetime) -> str:
        """
        从datetime对象生成日期路径
        格式: YYYY/MM/DD
        """
        return dt.strftime("%Y/%m/%d")

    def migrate_file(self, old_path: str, new_path: str) -> bool:
        """
        迁移单个文件
        
        Args:
            old_path: 原文件路径
            new_path: 新文件路径
            
        Returns:
            bool: 迁移是否成功
        """
        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            
            # 移动文件
            shutil.move(old_path, new_path)
            return True
        except Exception as e:
            self.errors.append(f"迁移文件 {old_path} 到 {new_path} 失败: {str(e)}")
            self.error_count += 1
            return False

    def migrate_uploaded_files(self, db: Session) -> dict:
        """
        迁移数据库中记录的上传文件
        
        Args:
            db: 数据库会话
            
        Returns:
            dict: 迁移结果统计
        """
        try:
            # 获取所有上传文件记录
            uploaded_files = db.query(UploadedFile).all()
            
            for file_record in uploaded_files:
                old_path = file_record.file_path
                
                # 检查文件是否存在
                if not os.path.exists(old_path):
                    self.errors.append(f"文件不存在: {old_path}")
                    self.error_count += 1
                    continue
                
                # 从文件记录的创建时间生成新路径
                created_date = file_record.created_at
                date_path = self.get_date_path_from_datetime(created_date)
                
                # 提取文件名
                filename = os.path.basename(old_path)
                new_path = os.path.join(self.base_dir, date_path, filename)
                
                # 如果已经在正确位置，跳过
                if old_path == new_path:
                    continue
                
                # 迁移文件
                if self.migrate_file(old_path, new_path):
                    # 更新数据库记录
                    file_record.file_path = new_path
                    self.migrated_count += 1
            
            # 提交数据库更改
            db.commit()
            
            return {
                "success": True,
                "migrated_count": self.migrated_count,
                "error_count": self.error_count,
                "errors": self.errors
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": str(e),
                "migrated_count": self.migrated_count,
                "error_count": self.error_count,
                "errors": self.errors
            }

    def migrate_orphan_files(self) -> dict:
        """
        迁移孤儿文件（直接在uploads目录下但不在数据库中的文件）
        """
        orphan_migrated = 0
        orphan_errors = []
        
        try:
            # 检查uploads根目录下的文件
            for item in os.listdir(self.base_dir):
                item_path = os.path.join(self.base_dir, item)
                
                # 只处理文件，不处理目录
                if os.path.isfile(item_path):
                    # 获取文件的修改时间作为创建日期
                    mtime = os.path.getmtime(item_path)
                    created_date = datetime.fromtimestamp(mtime)
                    date_path = self.get_date_path_from_datetime(created_date)
                    
                    new_path = os.path.join(self.base_dir, date_path, item)
                    
                    if self.migrate_file(item_path, new_path):
                        orphan_migrated += 1
                    else:
                        orphan_errors.append(f"迁移孤儿文件 {item_path} 失败")
            
            return {
                "success": True,
                "orphan_migrated": orphan_migrated,
                "orphan_errors": orphan_errors
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "orphan_migrated": orphan_migrated,
                "orphan_errors": orphan_errors
            }

    def full_migration(self, db: Session) -> dict:
        """
        执行完整的文件迁移
        
        Args:
            db: 数据库会话
            
        Returns:
            dict: 完整的迁移结果
        """
        print("开始文件迁移...")
        
        # 迁移数据库中的文件
        db_result = self.migrate_uploaded_files(db)
        print(f"数据库文件迁移完成: {db_result['migrated_count']} 个文件")
        
        # 迁移孤儿文件
        orphan_result = self.migrate_orphan_files()
        print(f"孤儿文件迁移完成: {orphan_result.get('orphan_migrated', 0)} 个文件")
        
        return {
            "database_migration": db_result,
            "orphan_migration": orphan_result,
            "total_migrated": self.migrated_count + orphan_result.get('orphan_migrated', 0),
            "total_errors": self.error_count + len(orphan_result.get('orphan_errors', []))
        }

def run_migration():
    """
    运行文件迁移的便捷函数
    """
    migrator = FileMigrator()
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        result = migrator.full_migration(db)
        
        print("\n=== 迁移完成 ===")
        print(f"总计迁移文件: {result['total_migrated']}")
        print(f"总计错误: {result['total_errors']}")
        
        if result['total_errors'] > 0:
            print("\n错误详情:")
            for error in migrator.errors:
                print(f"  - {error}")
        
        return result
        
    finally:
        db.close()

if __name__ == "__main__":
    run_migration() 