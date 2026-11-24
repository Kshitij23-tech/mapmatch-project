import subprocess
import sys

STEPS = ["src.preprocess", "src.graph", "src.labels", "src.measure_real", "src.sim_check", "src.train_sim",
         "src.eval_real", "src.flyover", "src.failures", "src.make_maps", "src.make_figures", "src.make_summary"]
for step in STEPS:
    print("\n=== running", step, flush=True)
    subprocess.run([sys.executable, "-m", step], check=True)
print("\nAll steps finished. Results are in the results folder.")