class TicketNotFoundError(Exception):
    def __init__(self, ticket_id: str):
        self.ticket_id = ticket_id