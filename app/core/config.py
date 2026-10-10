from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="payment_", extra="ignore", env_file=".env")

    debug: bool = False
    stage: str = "dev"
    port: int = 8081
    api_key: str = "test-api-key"

    outbox_worker_interval_seconds: int = 1

    db_driver: str = "postgresql+asyncpg"
    db_host: str = ""
    db_port: int = 5432
    db_user: str = ""
    db_password: str = ""
    db_name: str = ""

    @property
    def db_url(self) -> str:
        return (
            f"{self.db_driver}://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )

    db_ssl_mode: str = "disable"
    db_ssl_cert: str = ""
    db_logs: bool = False
    db_pool_size: int = 10
    db_max_overflow: int = 20

    rabbit_service_name: str = "rabbitmq"
    rabbit_user: str = ""
    rabbit_pass: str = ""
    rabbit_port: int = 5672

    @property
    def amqp_url(self) -> str:
        return (
            f"amqp://{self.rabbit_user}:"
            f"{self.rabbit_pass}@"
            f"{self.rabbit_service_name}:"
            f"{self.rabbit_port}/"
        )


settings = Settings()
