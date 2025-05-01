# Datei: src/core/estimator.py
from utils.config import MATERIAL_PRICES

class PriceEstimator:
    def __init__(self, material: str, quantity: int):
        self.material = material
        self.quantity = quantity
        self.price_per_cm3 = MATERIAL_PRICES.get(material, 0.15)
        self.labor_cost_per_hour = 45.00
        self.print_speed_cm3_per_hour = 5.0

    def calculate(self, volume_mm3: float) -> dict:
        volume_cm3 = volume_mm3 / 1000.0
        total_vol = volume_cm3 * self.quantity
        material_cost = total_vol * self.price_per_cm3
        print_time_h = total_vol / self.print_speed_cm3_per_hour
        labor_cost = print_time_h * self.labor_cost_per_hour
        total_cost = material_cost + labor_cost
        return {
            "volume_cm3": volume_cm3,
            "material_cost": material_cost,
            "print_time_h": print_time_h,
            "labor_cost": labor_cost,
            "total_cost": total_cost
        }