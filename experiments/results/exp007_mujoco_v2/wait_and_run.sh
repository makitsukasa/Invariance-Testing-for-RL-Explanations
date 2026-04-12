#!/bin/bash
OUT="/c/Users/tsukasa/Documents/oh-my-claudecode/experiments/results/exp007_mujoco_v2"
cd /c/Users/tsukasa/Documents/oh-my-claudecode

echo "[wait_and_run] 監視開始: $(date)"
while true; do
  all_done=1
  for seed in 123 456 789 1011; do
    if [ ! -f "$OUT/intuitive_hopper_seed${seed}.zip" ]; then
      all_done=0
      echo "[wait_and_run] $(date): seed=${seed} 未完了"
      break
    fi
  done
  if [ "$all_done" = "1" ]; then
    echo "[wait_and_run] 全モデル完了: $(date)"
    break
  fi
  sleep 120
done

echo "[wait_and_run] 蒸留・評価を開始: $(date)"
.venv/Scripts/python.exe experiments/run.py --config experiments/configs/exp007_mujoco_v2.yaml > "$OUT/run_final.log" 2>&1
echo "[wait_and_run] 実験完了 (exit=$?): $(date)"
