class Filter:
    def outlet(self, body, user=None):
        body["messages"][-1]["content"] += "!!!"
        return body