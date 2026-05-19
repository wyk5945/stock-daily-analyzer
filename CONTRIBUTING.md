# 贡献指南

## 开发环境

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## 质量检查

```bash
ruff check .
pytest -q
```

## 提交规范

- 变更保持最小、可审查
- 新功能必须带最小测试
- 不要提交任何密钥、Token、个人隐私信息

