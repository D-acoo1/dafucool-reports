# 可视化数据报告

[打开报告站](https://d-acoo1.github.io/dafucool-reports/)

首页按每份报告的内容更新时间倒序排列，时间使用北京时间。报告文件名就是它的固定地址。`reports.json` 维护标题、更新时间和旧地址映射。

## 发布报告

先打开站点搜索报告主题，核对是否属于同一份报告的更新。更新时用已登记的 HTML 文件名，新报告首次登记时选一个长期使用的文件名。参数里的源文件应为核验过的公开版。会用到的图表数据也需要检查，因为网页源文件可直接下载。

```bash
./sync_reports.sh /absolute/path/report.html existing-report.html
./sync_reports.sh /absolute/path/report.html new-report.html '新报告标题'
```

发布历史报告时可以用第四个参数传入带时区的原内容更新时间，例如 `2026-11-26T10:30:00+08:00`。内容相同的重试沿用站内时间。需要附带图表资源时，将经过检查的文件和对应报告、`reports.json`、生成后的 `index.html` 放进同一次提交。运行 `python3 generate_index.py` 可按登记重建首页。

推送后回查线上首页和报告直达链接，核对标题、更新时间和图表。旧版链接的跳转由对应 HTML 文件和目录里的旧地址映射提供。
