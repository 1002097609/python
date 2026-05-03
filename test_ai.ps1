$body = @{
    title = "测试护肤精华种草"
    content = "姐妹们！这款精华真的太好用了，连续用了28天，皮肤状态明显改善。成分党必看，5%烟酰胺浓度刚刚好，敏感肌也能用。质地清爽不油腻，吸收超快。对比了市面上10款同类产品，这款性价比排第一！回购了3次，闭眼入不会错。"
    platform = "抖音"
    category = ""
} | ConvertTo-Json -Compress

try {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:8081/api/dismantle/ai-analyze" -Method POST -ContentType "application/json; charset=utf8" -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 60
    Write-Host "=== AI 拆解结果 ==="
    Write-Host "L1 主题: $($r.l1_topic)"
    Write-Host "L1 核心卖点: $($r.l1_core_point)"
    Write-Host "L2 策略: $($r.l2_strategy -join ', ')"
    Write-Host "L2 情绪: $($r.l2_emotion)"
    Write-Host "L3 结构:"
    foreach ($s in $r.l3_structure) { Write-Host "  - $($s.name) ($($s.ratio)%): $($s.function)" }
    Write-Host "L4 标题公式: $($r.l4_elements.title_formula)"
    Write-Host "L4 钩子: $($r.l4_elements.hook)"
    Write-Host "L5 金句: $($r.l5_expressions.golden_sentences -join ', ')"
    Write-Host ""
    Write-Host "Meta: 品类=$($r._meta.detected_category), 结构=$($r._meta.structure_type), 降级=$($r._meta._fallback)"
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
}
