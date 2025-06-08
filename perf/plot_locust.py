import pandas as pd
import matplotlib.pyplot as plt

# читаємо історичний CSV з усіма кроками вимірювань
df = pd.read_csv("load_api_stats_history.csv")

# будуємо лінійний графік середнього часу відповіді
plt.plot(df["Total Average Response Time"], label="Avg response time")

# підписи осей і заголовок
plt.xlabel("Tact (seconds)")
plt.ylabel("Latency (ms)")
plt.title("Load test – 10 VU over 60s")

# легенда (якщо потрібно)
plt.legend()

# підганяємо макет і зберігаємо малюнок
plt.tight_layout()
plt.savefig("latency.png", dpi=150)

