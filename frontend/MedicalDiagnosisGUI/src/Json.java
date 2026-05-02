import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class Json {
    public static Object parse(String source) {
        return new Parser(source).parseValue();
    }

    public static String stringify(Object value) {
        if (value == null) {
            return "null";
        }
        if (value instanceof String text) {
            return "\"" + escape(text) + "\"";
        }
        if (value instanceof Number || value instanceof Boolean) {
            return String.valueOf(value);
        }
        if (value instanceof Map<?, ?> map) {
            List<String> parts = new ArrayList<>();
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                Object entryValue = entry.getValue();
                if (entryValue != null) {
                    parts.add(stringify(String.valueOf(entry.getKey())) + ":" + stringify(entryValue));
                }
            }
            return "{" + String.join(",", parts) + "}";
        }
        if (value instanceof Iterable<?> iterable) {
            List<String> parts = new ArrayList<>();
            for (Object item : iterable) {
                parts.add(stringify(item));
            }
            return "[" + String.join(",", parts) + "]";
        }
        return stringify(String.valueOf(value));
    }

    public static String asString(Object value) {
        if (value == null) {
            return "";
        }
        if (value instanceof Double number && number % 1 == 0) {
            return String.valueOf(number.longValue());
        }
        return String.valueOf(value);
    }

    public static double asDouble(Object value) {
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        try {
            return Double.parseDouble(asString(value));
        } catch (Exception e) {
            return 0.0;
        }
    }

    @SuppressWarnings("unchecked")
    public static Map<String, Object> asObject(Object value) {
        if (value instanceof Map<?, ?>) {
            return (Map<String, Object>) value;
        }
        return new LinkedHashMap<>();
    }

    @SuppressWarnings("unchecked")
    public static List<Map<String, Object>> asListOfObjects(Object value) {
        List<Map<String, Object>> result = new ArrayList<>();
        if (value instanceof List<?> list) {
            for (Object item : list) {
                if (item instanceof Map<?, ?>) {
                    result.add((Map<String, Object>) item);
                }
            }
        }
        return result;
    }

    @SuppressWarnings("unchecked")
    public static List<Object> asList(Object value) {
        if (value instanceof List<?> list) {
            return (List<Object>) list;
        }
        return new ArrayList<>();
    }

    private static String escape(String value) {
        return value.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r");
    }

    private static class Parser {
        private final String source;
        private int index = 0;

        Parser(String source) {
            this.source = source == null ? "" : source;
        }

        Object parseValue() {
            skipWhitespace();
            if (index >= source.length()) {
                return null;
            }
            char ch = source.charAt(index);
            if (ch == '{') {
                return parseObject();
            }
            if (ch == '[') {
                return parseArray();
            }
            if (ch == '"') {
                return parseString();
            }
            if (source.startsWith("true", index)) {
                index += 4;
                return true;
            }
            if (source.startsWith("false", index)) {
                index += 5;
                return false;
            }
            if (source.startsWith("null", index)) {
                index += 4;
                return null;
            }
            return parseNumber();
        }

        private Map<String, Object> parseObject() {
            Map<String, Object> map = new LinkedHashMap<>();
            index++;
            skipWhitespace();
            while (index < source.length() && source.charAt(index) != '}') {
                String key = parseString();
                skipWhitespace();
                expect(':');
                Object value = parseValue();
                map.put(key, value);
                skipWhitespace();
                if (peek(',')) {
                    index++;
                    skipWhitespace();
                }
            }
            expect('}');
            return map;
        }

        private List<Object> parseArray() {
            List<Object> list = new ArrayList<>();
            index++;
            skipWhitespace();
            while (index < source.length() && source.charAt(index) != ']') {
                list.add(parseValue());
                skipWhitespace();
                if (peek(',')) {
                    index++;
                    skipWhitespace();
                }
            }
            expect(']');
            return list;
        }

        private String parseString() {
            expect('"');
            StringBuilder builder = new StringBuilder();
            while (index < source.length()) {
                char ch = source.charAt(index++);
                if (ch == '"') {
                    break;
                }
                if (ch == '\\' && index < source.length()) {
                    char escaped = source.charAt(index++);
                    switch (escaped) {
                        case '"' -> builder.append('"');
                        case '\\' -> builder.append('\\');
                        case '/' -> builder.append('/');
                        case 'b' -> builder.append('\b');
                        case 'f' -> builder.append('\f');
                        case 'n' -> builder.append('\n');
                        case 'r' -> builder.append('\r');
                        case 't' -> builder.append('\t');
                        case 'u' -> {
                            String hex = source.substring(index, Math.min(index + 4, source.length()));
                            builder.append((char) Integer.parseInt(hex, 16));
                            index += 4;
                        }
                        default -> builder.append(escaped);
                    }
                } else {
                    builder.append(ch);
                }
            }
            return builder.toString();
        }

        private Number parseNumber() {
            int start = index;
            while (index < source.length()) {
                char ch = source.charAt(index);
                if (!(Character.isDigit(ch) || ch == '-' || ch == '+' || ch == '.' || ch == 'e' || ch == 'E')) {
                    break;
                }
                index++;
            }
            String token = source.substring(start, index);
            if (token.contains(".") || token.contains("e") || token.contains("E")) {
                return Double.parseDouble(token);
            }
            try {
                return Integer.parseInt(token);
            } catch (NumberFormatException e) {
                return Long.parseLong(token);
            }
        }

        private void expect(char expected) {
            skipWhitespace();
            if (index >= source.length() || source.charAt(index) != expected) {
                throw new IllegalArgumentException("Invalid JSON near index " + index);
            }
            index++;
        }

        private boolean peek(char expected) {
            return index < source.length() && source.charAt(index) == expected;
        }

        private void skipWhitespace() {
            while (index < source.length() && Character.isWhitespace(source.charAt(index))) {
                index++;
            }
        }
    }
}
