# [重要/漏洞：aaPanel](https://github.com/myogg/Gitblog/issues/95)

重要/漏洞：aaPanel（宝塔面板）数据库权限查询逻辑存在 SQL 注入漏洞

漏洞编号：CVE-2025-12914 
重要等级：需要注意的（中危）
CVSS 分数：4.7（CVSS v3.1） / 5.1（CVSS v4.0）

影响范围：
面板版本：≤ 11.2.x

漏洞原理: 该漏洞出现在受影响的宝塔面板版本的 数据库权限查询逻辑 中，在处理
/database?action=GetDatabaseAccess 接口时，对参数 Name 的校验不足：

旧代码通过 字符串拼接 构造 SQL：
users = mysql_obj.query(
    "select Host from mysql.user where User='" + name + "' AND Host!='localhost'"
)
攻击者在满足一定权限（或 API AccessKey）的前提下，如果能控制 name，即可通过构造特殊输入触发 SQL 注入。

注意: 宝塔官方解释此漏洞 不能被未授权的远程用户直接利用，必须先拿到 宝塔后台管理员账号或面板 API AccessKey，才能进一步利用。
实际上该漏洞属于“高权限条件下进一步放大风险”的漏洞，而不是“扫到就 RCE/沦陷”那种高危漏洞。目前公开信息显示，相关利用细节已被安全社区披露，NVD 条目中也明确该漏洞已对外公开并可被利用。

受影响组件: 
宝塔面板（aaPanel / BaoTa Panel）Backend 模块
具体接口：/database?action=GetDatabaseAccess
受影响参数：Name

处置建议：
面板统一升级到 11.3.0 或更新版本。如暂时无法升级，可采取：
限制面板访问来源 IP
启用双因素认证
检查面板 API 与 MySQL 日志

参考资料: [NVD](https://nvd.nist.gov/vuln/detail/CVE-2025-12914)