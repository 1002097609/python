"""
Tag → Option 数据迁移脚本（backend/migrate_tag_option.py）。

用途：
  将 tag 表中 type 为 category/platform/style/strategy 的记录，
  关联到 option 表中对应的记录，填充 tag.option_id 字段。

用法：
  python -c "from backend.migrate_tag_option import migrate; migrate()"

注意：
  - 此脚本应在模型变更（加 option_id 字段）后执行
  - 使用"存在则更新"策略，可重复运行
  - 对于找不到匹配 option 的 tag 记录，打印警告但不中断
"""

from backend.database import SessionLocal
from backend.models.tag import Tag
from backend.models.option import Option

SYNC_TYPES = {"category", "platform", "style", "strategy"}


def migrate():
    """
    执行 tag → option 的关联迁移。

    流程：
    1. 查询 tag 表中所有 type 在 SYNC_TYPES 中且 option_id 为空的记录
    2. 对每条 tag，在 option 表中查找 (group_key=tag.type, value=tag.name) 的记录
    3. 找到则更新 tag.option_id
    4. 找不到则打印警告
    """
    db = SessionLocal()
    try:
        tags = db.query(Tag).filter(Tag.type.in_(SYNC_TYPES)).all()
        linked = 0
        skipped = 0
        warnings = 0

        for tag in tags:
            if tag.option_id is not None:
                skipped += 1
                continue

            opt = (
                db.query(Option)
                .filter(Option.group_key == tag.type, Option.value == tag.name)
                .first()
            )
            if opt:
                tag.option_id = opt.id
                linked += 1
            else:
                print(f"  [WARN] tag id={tag.id} name={tag.name!r} type={tag.type!r} — 在 option 表中无匹配记录")
                warnings += 1

        db.commit()
        print(f"[OK] 迁移完成：关联 {linked} 条，跳过（已有）{skipped} 条，警告 {warnings} 条，共 {len(tags)} 条")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
