# 快速保存当前代码到GitHub
# 用法: .\quick-save.ps1 "修改说明"

param(
    [string]$message = "快速保存: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
)

Write-Host "正在保存代码..." -ForegroundColor Green

# 添加所有修改
git add -A

# 提交
git commit -m $message

# 推送到GitHub
git push

Write-Host "✅ 保存完成！已推送到GitHub" -ForegroundColor Green
