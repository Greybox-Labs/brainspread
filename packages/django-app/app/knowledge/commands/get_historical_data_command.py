from common.commands.abstract_base_command import AbstractBaseCommand
from ..repositories.historical_repository import HistoricalRepository


class GetHistoricalDataCommand(AbstractBaseCommand):
    """Command to retrieve historical pages and blocks data"""

    def __init__(self, user, days_back=30, limit=50):
        self.user = user
        self.days_back = days_back
        self.limit = limit
        self.repository = HistoricalRepository()

    def execute(self):
        """Execute the command and return historical data"""
        return self.repository.get_historical_data(
            user=self.user,
            days_back=self.days_back,
            limit=self.limit
        )