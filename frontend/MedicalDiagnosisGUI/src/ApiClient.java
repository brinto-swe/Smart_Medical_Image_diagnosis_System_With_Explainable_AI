import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class ApiClient {
    private final String baseUrl;
    private final HttpClient http = HttpClient.newHttpClient();
    private String token;

    public ApiClient(String baseUrl) {
        this.baseUrl = baseUrl;
    }

    public void setToken(String token) {
        this.token = token;
    }

    public Map<String, Object> login(String username, String password) throws Exception {
        Map<String, Object> response = postJson("/api/auth/login/", Map.of("username", username, "password", password));
        setToken(Json.asString(response.get("token")));
        return response;
    }

    public Map<String, Object> getObject(String path) throws Exception {
        Object parsed = send("GET", path, (byte[]) null, "application/json");
        return Json.asObject(parsed);
    }

    public List<Map<String, Object>> getList(String path) throws Exception {
        Object parsed = send("GET", path, (byte[]) null, "application/json");
        return Json.asListOfObjects(parsed);
    }

    public Map<String, Object> postJson(String path, Map<String, Object> body) throws Exception {
        Object parsed = send("POST", path, Json.stringify(body), "application/json");
        return Json.asObject(parsed);
    }

    public Map<String, Object> patchJson(String path, Map<String, Object> body) throws Exception {
        Object parsed = send("PATCH", path, Json.stringify(body), "application/json");
        return Json.asObject(parsed);
    }

    public void delete(String path) throws Exception {
        send("DELETE", path, (byte[]) null, "application/json");
    }

    public Map<String, Object> patchMultipart(String path, Map<String, Object> fields, String fileField, File file) throws Exception {
        Map<String, File> files = new java.util.LinkedHashMap<>();
        if (fileField != null && file != null) {
            files.put(fileField, file);
        }
        return patchMultipart(path, fields, files);
    }

    public Map<String, Object> patchMultipart(String path, Map<String, Object> fields, Map<String, File> files) throws Exception {
        String boundary = "----MediCareBoundary" + System.currentTimeMillis();
        List<byte[]> chunks = new ArrayList<>();
        for (Map.Entry<String, Object> entry : fields.entrySet()) {
            if (entry.getValue() != null) {
                addField(chunks, boundary, entry.getKey(), String.valueOf(entry.getValue()));
            }
        }
        for (Map.Entry<String, File> entry : files.entrySet()) {
            if (entry.getValue() != null) {
                addFile(chunks, boundary, entry.getKey(), entry.getValue());
            }
        }
        chunks.add(("--" + boundary + "--\r\n").getBytes(StandardCharsets.UTF_8));

        int size = chunks.stream().mapToInt(bytes -> bytes.length).sum();
        byte[] body = new byte[size];
        int offset = 0;
        for (byte[] chunk : chunks) {
            System.arraycopy(chunk, 0, body, offset, chunk.length);
            offset += chunk.length;
        }

        Object parsed = send("PATCH", path, body, "multipart/form-data; boundary=" + boundary);
        return Json.asObject(parsed);
    }

    public void downloadToFile(String path, File target) throws Exception {
        HttpRequest.Builder builder = HttpRequest.newBuilder(URI.create(baseUrl + path));
        if (token != null && !token.isBlank()) {
            builder.header("Authorization", "Token " + token);
        }
        HttpResponse<byte[]> response = http.send(builder.GET().build(), HttpResponse.BodyHandlers.ofByteArray());
        if (response.statusCode() >= 400) {
            Object parsed = response.body() == null || response.body().length == 0
                ? Map.of()
                : Json.parse(new String(response.body(), StandardCharsets.UTF_8));
            throw new RuntimeException(errorMessage(parsed, response.statusCode()));
        }
        Files.write(target.toPath(), response.body());
    }

    public File downloadToTempFile(String path, String prefix, String suffix) throws Exception {
        Path target = Files.createTempFile(prefix, suffix);
        downloadToFile(path, target.toFile());
        return target.toFile();
    }

    public Map<String, Object> uploadXray(String patientId, File image) throws Exception {
        String boundary = "----MediCareBoundary" + System.currentTimeMillis();
        List<byte[]> chunks = new ArrayList<>();
        addField(chunks, boundary, "patient_id", patientId);
        addFile(chunks, boundary, "image", image);
        chunks.add(("--" + boundary + "--\r\n").getBytes(StandardCharsets.UTF_8));

        int size = chunks.stream().mapToInt(bytes -> bytes.length).sum();
        byte[] body = new byte[size];
        int offset = 0;
        for (byte[] chunk : chunks) {
            System.arraycopy(chunk, 0, body, offset, chunk.length);
            offset += chunk.length;
        }

        Object parsed = send("POST", "/api/doctor/xray/upload/", body, "multipart/form-data; boundary=" + boundary);
        return Json.asObject(parsed);
    }

    private void addField(List<byte[]> chunks, String boundary, String name, String value) {
        chunks.add(("--" + boundary + "\r\n").getBytes(StandardCharsets.UTF_8));
        chunks.add(("Content-Disposition: form-data; name=\"" + name + "\"\r\n\r\n").getBytes(StandardCharsets.UTF_8));
        chunks.add((value + "\r\n").getBytes(StandardCharsets.UTF_8));
    }

    private void addFile(List<byte[]> chunks, String boundary, String name, File file) throws IOException {
        chunks.add(("--" + boundary + "\r\n").getBytes(StandardCharsets.UTF_8));
        chunks.add(("Content-Disposition: form-data; name=\"" + name + "\"; filename=\"" + file.getName() + "\"\r\n").getBytes(StandardCharsets.UTF_8));
        chunks.add(("Content-Type: application/octet-stream\r\n\r\n").getBytes(StandardCharsets.UTF_8));
        chunks.add(Files.readAllBytes(file.toPath()));
        chunks.add("\r\n".getBytes(StandardCharsets.UTF_8));
    }

    private Object send(String method, String path, String body, String contentType) throws Exception {
        byte[] bytes = body == null ? null : body.getBytes(StandardCharsets.UTF_8);
        return send(method, path, bytes, contentType);
    }

    private Object send(String method, String path, byte[] body, String contentType) throws Exception {
        HttpRequest.Builder builder = HttpRequest.newBuilder(URI.create(baseUrl + path));
        builder.header("Accept", "application/json");
        if (token != null && !token.isBlank()) {
            builder.header("Authorization", "Token " + token);
        }
        if (body == null) {
            builder.method(method, HttpRequest.BodyPublishers.noBody());
        } else {
            builder.header("Content-Type", contentType);
            builder.method(method, HttpRequest.BodyPublishers.ofByteArray(body));
        }

        HttpResponse<String> response = http.send(builder.build(), HttpResponse.BodyHandlers.ofString());
        Object parsed = response.body() == null || response.body().isBlank() ? Map.of() : Json.parse(response.body());
        if (response.statusCode() >= 400) {
            throw new RuntimeException(errorMessage(parsed, response.statusCode()));
        }
        return parsed;
    }

    private String errorMessage(Object parsed, int status) {
        if (parsed instanceof Map<?, ?> map) {
            Object error = map.get("error");
            if (error != null) {
                return Json.asString(error);
            }
            Object detail = map.get("detail");
            if (detail != null) {
                return Json.asString(detail);
            }
            return map.toString();
        }
        return "Request failed with status " + status;
    }

    public static String urlEncode(String value) {
        return URLEncoder.encode(value == null ? "" : value, StandardCharsets.UTF_8);
    }
}
