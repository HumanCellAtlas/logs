import json


def extract_json(message):
        """
            Returns extracted JSON if valid or None if not found or invalid from data string

            Args:
            data (string): Input log event data

            Output:
            dict
        """
        json_bound_loci = extract_json_bounds(message)
        beginning_index = json_bound_loci[0]
        end_index = json_bound_loci[1]
        if beginning_index is not None and end_index is not None:
            try:
                formatted_data = message[beginning_index:end_index + 1]
                json_body = json.loads(formatted_data)
                return json_body
            except:
                return {}
        return {}


def extract_json_bounds(message):
    """
        Returns indices for opening and closing brackets in incoming data string

        Args:
        data (string): Input log event data

        Returns
        (beginning_index, end_index)

    """
    beginning_index = None
    unclosed_brace_count = 0
    end_index = None

    for idx, char in enumerate(message):
        if char == "{":
            unclosed_brace_count += 1
            if beginning_index is None:
                beginning_index = idx
        elif char == "}":
            unclosed_brace_count -= 1
            if beginning_index is not None and end_index is None and unclosed_brace_count == 0:
                end_index = idx
                break

    return beginning_index, end_index