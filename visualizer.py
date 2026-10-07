import matplotlib.pyplot as plt
import numpy as np
import csv
from pathlib import Path

#Load data from prices.csv
data = [[], [], [], []]  # min, avg, max

x_axis = np.array(range(30))

BASE_DIR = Path(__file__).resolve().parent
CSV = BASE_DIR / "prices.csv"

with open(CSV, "r") as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        data[0].append(float(row[0]))  # min price
        data[1].append(float(row[1]))  # avg price
        data[2].append(float(row[2]))  # max price

plt.figure()

plt.plot(x_axis, data[0], label="Min price")
plt.plot(x_axis, data[1], label="Avg price")
plt.plot(x_axis, data[2], label="Max price")

rolling_average = np.convolve(data[1], np.ones(4)/4, mode='valid')

plt.plot(range(3, 30), rolling_average, label="3-day Rolling Avg", linestyle='--')

plt.xlabel("Date")
plt.ylabel("Price (€)")
plt.title("Train prices over time")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.grid(True)

plt.show()