# 健康检查并尝试自动修复
npx ruflo doctor --fix

# 初始化向量嵌入数据库
npx ruflo embeddings init

# 初始化 Hive-Mind，并设置网络拓扑为层级结构
npx ruflo hive-mind init --topology hierarchical

# 初始化 Swarm，并使用 V3 模式
npx ruflo swarm init --v3-mode --topology hierarchical

npx ruflo mcp start --daemon

npx ruflo hive-mind status
npx ruflo swarm status
npx ruflo mcp status

claude mcp add ruflo -- npx -y ruflo@latest mcp start

npx ruflo init --wizard

ruflo daemon start
ruflo memory init
ruflo swarm init
ruflo init --start-all
