#!/bin/bash
# API test script
pkill -f "uvicorn main:app" 2>/dev/null
sleep 1

cd /Users/fushuaiguo/Documents/work/2026-08-02-00-12-34/api
export PYTHONPATH=/Users/fushuaiguo/Documents/work/2026-08-02-00-12-34/api
/Users/fushuaiguo/.workbuddy/binaries/python/envs/restart_api/bin/uvicorn main:app --host 127.0.0.1 --port 8000 &
UVPID=$!
sleep 3

echo "=== 0. Health ==="
curl -s http://127.0.0.1:8000/api/health
echo ""

echo "=== 1. Register ==="
REG=$(curl -s -X POST http://127.0.0.1:8000/api/auth/register -H "Content-Type: application/json" -d '{"email":"test3@restart.org","password":"123456","nickname":"test3"}')
echo "$REG"
TOKEN=$(echo "$REG" | /Users/fushuaiguo/.workbuddy/binaries/python/envs/restart_api/bin/python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "=== 1b. Login ==="
  REG=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login -H "Content-Type: application/json" -d '{"email":"test3@restart.org","password":"123456"}')
  echo "$REG"
  TOKEN=$(echo "$REG" | /Users/fushuaiguo/.workbuddy/binaries/python/envs/restart_api/bin/python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
fi
echo "Token: ${TOKEN:0:30}..."
echo ""

echo "=== 2. Me ==="
curl -s http://127.0.0.1:8000/api/auth/me -H "Authorization: Bearer $TOKEN"
echo ""

echo "=== 3. Create Job ==="
curl -s -X POST http://127.0.0.1:8000/api/jobs -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"company":"腾讯","position":"后端开发","salary":"25-35k","status":"面试","apply_date":"2026-07-15","follow_date":"2026-08-06","feedback":"技术面通过"}'
echo ""

echo "=== 4. Job Stats ==="
curl -s http://127.0.0.1:8000/api/jobs/stats -H "Authorization: Bearer $TOKEN"
echo ""

echo "=== 5. Create Diary ==="
curl -s -X POST http://127.0.0.1:8000/api/diary -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"entry_date":"2026-08-06","mood":4,"achievement":"API测试通过"}'
echo ""

echo "=== 6. Create Transaction ==="
curl -s -X POST http://127.0.0.1:8000/api/finance -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"txn_type":"expense","amount":3500,"category":"住房","txn_date":"2026-08-01","note":"八月房租"}'
echo ""

echo "=== 7. Finance Summary ==="
curl -s http://127.0.0.1:8000/api/finance/summary -H "Authorization: Bearer $TOKEN"
echo ""

echo "=== 8. Create Skill ==="
curl -s -X POST http://127.0.0.1:8000/api/skills -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"LeetCode刷题","skill_type":"刷题","current_progress":45,"target_total":150,"daily_goal":"每天3题"}'
echo ""

echo "=== 9. Checkin ==="
SKILL_LIST=$(curl -s http://127.0.0.1:8000/api/skills -H "Authorization: Bearer $TOKEN")
echo "$SKILL_LIST" | /Users/fushuaiguo/.workbuddy/binaries/python/envs/restart_api/bin/python3 -c "import sys,json; d=json.load(sys.stdin); print(f'count={len(d)}, first_id={d[0][\"id\"] if d else 0}')"
SKILL_ID=$(echo "$SKILL_LIST" | /Users/fushuaiguo/.workbuddy/binaries/python/envs/restart_api/bin/python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'] if d else '')")
curl -s -X POST "http://127.0.0.1:8000/api/skills/$SKILL_ID/checkin" -H "Authorization: Bearer $TOKEN"
echo ""

echo "=== 10. Skills with Checkin ==="
curl -s http://127.0.0.1:8000/api/skills -H "Authorization: Bearer $TOKEN" | /Users/fushuaiguo/.workbuddy/binaries/python/envs/restart_api/bin/python3 -c "
import sys,json
d=json.load(sys.stdin)
for s in d:
    print(f'  {s[\"name\"]} | streak={s[\"streak\"]} | checkins={len(s[\"checkins\"])} | progress={s[\"current_progress\"]}/{s[\"target_total\"]}')
"
echo ""

echo "=== 11. Subscribe ==="
curl -s -X POST http://127.0.0.1:8000/api/subscribe -H "Content-Type: application/json" -d '{"email":"sub@test.org"}'
echo ""

echo "=== 12. Update Settings ==="
curl -s -X PUT http://127.0.0.1:8000/api/settings -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"unemployment_start":"2026-07-01","monthly_budget":5000,"savings":80000}'
echo ""

echo "=== 13. Get Settings ==="
curl -s http://127.0.0.1:8000/api/settings -H "Authorization: Bearer $TOKEN"
echo ""

echo "=== ALL DONE ==="
kill $UVPID 2>/dev/null
