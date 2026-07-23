from typing import Any


class ObjectMapper:
    @staticmethod
    def map_payload(payload: dict[str, Any]) -> dict[str, Any]:
        result = ObjectMapper._copy_value(payload)

        if not isinstance(result, dict):
            return result

        name = ObjectMapper._build_name(result)
        if name and "name" not in result:
            result["name"] = name

        # Only expose the DTO fields.
        return {
            key: result[key]
            for key in ("id", "name", "email")
            if key in result
        }

    @staticmethod
    def _copy_value(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: ObjectMapper._copy_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [ObjectMapper._copy_value(item) for item in value]
        return value

    @staticmethod
    def _build_name(data: dict[str, Any]) -> str | None:
        first_name = data.get("first_name") or data.get("firstName")
        last_name = data.get("last_name") or data.get("lastName")

        if first_name and last_name:
            return f"{first_name} {last_name}".strip()

        return None

