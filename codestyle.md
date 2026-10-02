# Backend Code Style

参考来源：

- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

## 本项目约定

- 使用 4 个空格缩进，不使用 Tab。
- 函数、变量使用 `snake_case`；类使用 `PascalCase`。
- 所有公共函数写清晰的类型标注。
- 路由只负责 HTTP 层逻辑，表达式计算放在 service 层。
- 异常必须转换为用户可理解的标准 API 错误。
- 数据库会话由依赖注入管理，避免在路由中创建全局连接。
- 测试文件使用 `test_*.py` 命名，并覆盖正常、异常和边界情况。
- 禁止使用 `eval`、`exec` 或其他任意代码执行方式处理用户表达式。
