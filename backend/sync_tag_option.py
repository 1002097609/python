"""
Tag ↔ Option 一次性同步脚本（backend/sync_tag_option.py）。

用途：
  将 tag 表中 type 为 category/platform/style/strategy 的记录
  同步到 option 表中，确保两个数据源一致。

用法：
  python -c "from backend.sync_tag_option import sync_all; sync_all()"

注意：
  - 使用 upsert 模式，不会重复创建已存在的记录
  - 此脚本用于修复历史数据，通常在部署 tag/option 双向同步功能后执行一次
"""

from backend.database import SessionLocal
from backend.models.tag import Tag
from backend.models.option import Option

SYNC_TYPES = {"category", "platform", "style", "strategy"}


def sync_all():
    """
    执行 tag → option 的全量同步。

    流程：
    1. 查询 tag 表中所有 type 在 SYNC_TYPES 中的记录
    2. 对每条 tag，在 option 表中查找 (group_key=tag.type, value=tag.name)
    3. 如果不存在则插入，存在则更新 label
    """
    db = SessionLocal()
    try:
        tags = db.query(Tag).filter(Tag.type.in_(SYNC_TYPES)).all()
        inserted = 0
        updated = 0

        for tag in tags:
            opt = (
                db.query(Option)
                .filter(Option.group_key == tag.type, Option.value == tag.name)
                .first()
            )
            if opt:
                opt.label = tag.name
                updated += 1
            else:
                db.add(Option(
                    group_key=tag.type,
                    label=tag.name,
                    value=tag.name,
                    sort_order=0,
                    is_active=1,
                ))
                inserted += 1

        db.commit()
        print(f"[OK] Tag → Option 同步完成：插入 {inserted} 条，更新 {updated} 条，共处理 {len(tags)} 条")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
    finally:
        db.close()


if __name__ == "__main__":
    sync_all()
