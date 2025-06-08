from locust import HttpUser, task, between

class OrderApiUser(HttpUser):
    wait_time = between(0.2, 0.5)           # пауза між запитами
    host = "http://api:8000"                # ім'я сервісу у docker-compose
    token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzIiwiZXhwIjoxNzQ5Mzk1NzYzfQ.zJPPnEpgXwrFRsTlm0IGPZ3BYUolFxgLBC095e6RrOE"          # згенеруйте раз у Swagger

    @task
    def eta(self):
        self.client.get(
            "/api/v1/orders/1/eta",
            headers={"Authorization": self.token},
            name="/orders/{id}/eta"
        )

