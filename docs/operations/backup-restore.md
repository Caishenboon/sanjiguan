# 备份与恢复

## 手动备份

`BACKUP_DATABASE_URL` 只在执行进程环境中提供：

```bash
python scripts/backup.py --output /secure/backup-directory
```

脚本调用标准 `pg_dump --format=custom`，生成 Dump 与 SHA-256 Manifest。离开主机
前使用组织批准的工具加密，密钥与备份分开保存。不要自行设计加密算法。

## 恢复到空环境

```bash
RESTORE_DATABASE_URL=postgresql://.../empty_database \
  python scripts/restore.py /secure/backup-directory/sanjiguan-....manifest.json
```

脚本拒绝非空目标，先校验 Dump Hash，再调用 `pg_restore`，最后核对 migration、
三际录数量与 Hash 格式。恢复验证不依赖原数据库继续存在。

恢复后还必须检查登录、主体、三际录、代表性 Replay、DeepSeek 回退和 `/ready`。
离线旧备份中的删除资料会持续到保留期届满；系统不会伪称能即时修改离线副本。

建议小规模部署采用每日、每周、每月分层保留，并每季度向新空库做一次恢复演练。
