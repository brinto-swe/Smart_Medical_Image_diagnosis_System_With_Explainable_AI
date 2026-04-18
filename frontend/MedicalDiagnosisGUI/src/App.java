import java.io.File;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import javafx.application.Application;
import javafx.application.Platform;
import javafx.beans.property.SimpleStringProperty;
import javafx.collections.FXCollections;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.control.Alert;
import javafx.scene.control.Button;
import javafx.scene.control.ComboBox;
import javafx.scene.control.Label;
import javafx.scene.control.PasswordField;
import javafx.scene.control.ProgressIndicator;
import javafx.scene.control.ScrollPane;
import javafx.scene.control.Separator;
import javafx.scene.control.TableColumn;
import javafx.scene.control.TableView;
import javafx.scene.control.TextArea;
import javafx.scene.control.TextField;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.GridPane;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.Region;
import javafx.scene.layout.StackPane;
import javafx.scene.layout.VBox;
import javafx.stage.FileChooser;
import javafx.stage.Stage;

public class App extends Application {
    private static final String API_BASE_URL = "http://127.0.0.1:8000";

    private final ApiClient api = new ApiClient(API_BASE_URL);
    private Stage stage;
    private BorderPane shell;
    private Map<String, Object> currentUser;

    public static void main(String[] args) {
        launch(args);
    }

    @Override
    public void start(Stage primaryStage) {
        this.stage = primaryStage;
        Scene scene = new Scene(showLogin(), 1280, 760);
        scene.getStylesheets().add(stylesheet());
        stage.setTitle("MediCare");
        stage.setMinWidth(1100);
        stage.setMinHeight(700);
        stage.setScene(scene);
        stage.show();
    }

    private String stylesheet() {
        File css = new File("src/styles.css");
        return css.exists() ? css.toURI().toString() : getClass().getResource("styles.css").toExternalForm();
    }

    private Parent showLogin() {
        VBox root = new VBox(24);
        root.getStyleClass().add("login-root");
        root.setAlignment(Pos.CENTER);

        Label logo = new Label("L");
        logo.getStyleClass().add("login-logo");
        Label title = new Label("Medical Management System");
        title.getStyleClass().add("login-title");
        Label subtitle = new Label("Select your role to access the dashboard");
        subtitle.getStyleClass().add("muted");

        HBox roleCards = new HBox(20,
            roleCard("Administrator", "Manage doctors, patients, and system reports"),
            roleCard("Doctor", "Search patients, analyze X-rays, and view history"),
            roleCard("Patient", "View medical reports and manage your information")
        );
        roleCards.setAlignment(Pos.CENTER);

        VBox form = card();
        form.setMaxWidth(420);
        TextField username = input("Username");
        PasswordField password = passwordInput("Password");
        Button login = primaryButton("Login");
        Button signup = ghostButton("Create patient account");
        Button forgot = ghostButton("Forgot password");
        Label message = new Label();
        message.getStyleClass().add("error");

        login.setMaxWidth(Double.MAX_VALUE);
        signup.setMaxWidth(Double.MAX_VALUE);
        forgot.setMaxWidth(Double.MAX_VALUE);
        login.setOnAction(e -> runAsync(message, () -> {
            Map<String, Object> response = api.login(username.getText(), password.getText());
            currentUser = Json.asObject(response.get("user"));
            Platform.runLater(this::showDashboardForCurrentUser);
        }));
        signup.setOnAction(e -> stage.getScene().setRoot(showSignup()));
        forgot.setOnAction(e -> showPasswordResetRequest());

        form.getChildren().addAll(sectionTitle("Login"), username, password, login, signup, forgot, message);
        root.getChildren().addAll(logo, title, subtitle, roleCards, form);
        return root;
    }

    private Parent showSignup() {
        VBox root = new VBox(18);
        root.getStyleClass().add("login-root");
        root.setAlignment(Pos.CENTER);

        VBox form = card();
        form.setMaxWidth(520);
        TextField username = input("Username");
        TextField email = input("Email");
        TextField firstName = input("First name");
        TextField lastName = input("Last name");
        PasswordField password = passwordInput("Password");
        Label message = new Label();
        message.getStyleClass().add("error");
        Button submit = primaryButton("Create Patient Account");
        Button back = ghostButton("Back to login");

        submit.setMaxWidth(Double.MAX_VALUE);
        back.setMaxWidth(Double.MAX_VALUE);
        submit.setOnAction(e -> runAsync(message, () -> {
            Map<String, Object> body = Map.of(
                "username", username.getText(),
                "email", email.getText(),
                "first_name", firstName.getText(),
                "last_name", lastName.getText(),
                "password", password.getText()
            );
            Map<String, Object> response = api.postJson("/api/auth/signup/", body);
            api.setToken(Json.asString(response.get("token")));
            currentUser = Json.asObject(response.get("user"));
            Platform.runLater(this::showDashboardForCurrentUser);
        }));
        back.setOnAction(e -> stage.getScene().setRoot(showLogin()));

        form.getChildren().addAll(sectionTitle("Patient Signup"), username, email, firstName, lastName, password, submit, back, message);
        root.getChildren().add(form);
        return root;
    }

    private VBox roleCard(String title, String text) {
        VBox card = new VBox(12);
        card.getStyleClass().add("role-card");
        card.setAlignment(Pos.CENTER);
        card.setPrefWidth(260);
        Label icon = new Label(title.substring(0, 1));
        icon.getStyleClass().add("role-icon");
        Label heading = new Label(title);
        heading.getStyleClass().add("role-title");
        Label desc = new Label(text);
        desc.getStyleClass().add("role-desc");
        desc.setWrapText(true);
        card.getChildren().addAll(icon, heading, desc);
        return card;
    }

    private void showDashboardForCurrentUser() {
        String role = Json.asString(currentUser.get("role"));
        shell = new BorderPane();
        shell.getStyleClass().add("app-shell");
        shell.setLeft(sidebar(role));
        stage.getScene().setRoot(shell);

        switch (role) {
            case "admin" -> showAdminDashboard();
            case "doctor" -> showDoctorDashboard();
            default -> showPatientDashboard();
        }
    }

    private VBox sidebar(String role) {
        VBox nav = new VBox(8);
        nav.getStyleClass().add("sidebar");
        nav.setPrefWidth(170);

        Label brand = new Label("MediCare");
        brand.getStyleClass().add("brand");
        Label portal = new Label(capitalize(role) + " Portal");
        portal.getStyleClass().add("portal");
        VBox header = new VBox(2, brand, portal);
        header.setPadding(new Insets(16, 14, 16, 14));

        nav.getChildren().add(header);
        switch (role) {
            case "admin" -> nav.getChildren().addAll(
                navButton("Dashboard", this::showAdminDashboard),
                navButton("Manage Doctors", this::showManageDoctors),
                navButton("Manage Patients", this::showManagePatients),
                navButton("Reports", this::showAdminReports)
            );
            case "doctor" -> nav.getChildren().addAll(
                navButton("Dashboard", this::showDoctorDashboard),
                navButton("X-ray Analysis", this::showDoctorUpload),
                navButton("Patient History", this::showDoctorHistory)
            );
            default -> nav.getChildren().addAll(
                navButton("My Dashboard", this::showPatientDashboard),
                navButton("My Reports", this::showPatientReports),
                navButton("My Information", this::showProfile)
            );
        }

        Region spacer = new Region();
        VBox.setVgrow(spacer, Priority.ALWAYS);
        Button logout = navButton("Logout", () -> {
            runAsync(null, () -> {
                try {
                    api.postJson("/api/auth/logout/", Map.of());
                } catch (Exception ignored) {
                }
                api.setToken(null);
                currentUser = null;
                Platform.runLater(() -> stage.getScene().setRoot(showLogin()));
            });
        });
        nav.getChildren().addAll(spacer, logout);
        return nav;
    }

    private Button navButton(String text, Runnable action) {
        Button button = new Button(text);
        button.getStyleClass().add("nav-button");
        button.setMaxWidth(Double.MAX_VALUE);
        button.setOnAction(e -> action.run());
        return button;
    }

    private void setContent(String title, String subtitle, Parent content) {
        VBox page = new VBox(18);
        page.getStyleClass().add("page");
        HBox top = new HBox();
        top.setAlignment(Pos.CENTER_LEFT);
        VBox headings = new VBox(4, pageTitle(title), muted(subtitle));
        Region spacer = new Region();
        HBox.setHgrow(spacer, Priority.ALWAYS);
        Label date = muted(LocalDate.now().format(DateTimeFormatter.ofPattern("EEEE, MMMM d, yyyy")));
        top.getChildren().addAll(headings, spacer, date);

        ScrollPane scroll = new ScrollPane(content);
        scroll.setFitToWidth(true);
        scroll.getStyleClass().add("page-scroll");
        page.getChildren().addAll(top, scroll);
        shell.setCenter(page);
    }

    private void showAdminDashboard() {
        VBox content = new VBox(18);
        HBox stats = new HBox(16, statCard("Total Doctors", "-", "blue"), statCard("Total Patients", "-", "teal"));
        GridPane quick = new GridPane();
        quick.setHgap(18);
        quick.setVgap(18);
        quick.add(createDoctorForm(), 0, 0);
        quick.add(createPatientForm(), 1, 0);
        content.getChildren().addAll(stats, quick, sectionTitle("Recently Added Doctors"), doctorTable(List.of()));
        setContent("Admin Dashboard", "Manage your healthcare system", content);

        runAsync(null, () -> {
            Map<String, Object> summary = api.getObject("/api/admin/reports/summary/");
            List<Map<String, Object>> doctors = api.getList("/api/admin/doctors/");
            Platform.runLater(() -> {
                stats.getChildren().set(0, statCard("Total Doctors", Json.asString(summary.get("active_doctors")), "blue"));
                stats.getChildren().set(1, statCard("Total Patients", Json.asString(summary.get("total_patients")), "teal"));
                content.getChildren().set(3, doctorTable(doctors));
            });
        });
    }

    private void showManageDoctors() {
        VBox content = new VBox(18, createDoctorForm(), tableLoading());
        setContent("Manage Doctors", "Add, edit, and manage doctor profiles", content);
        runAsync(null, () -> {
            List<Map<String, Object>> doctors = api.getList("/api/admin/doctors/");
            Platform.runLater(() -> content.getChildren().set(1, doctorTable(doctors)));
        });
    }

    private void showManagePatients() {
        VBox content = new VBox(18, createPatientForm(), tableLoading());
        setContent("Manage Patients", "Add, edit, and manage patient records", content);
        runAsync(null, () -> {
            List<Map<String, Object>> patients = api.getList("/api/admin/patients/");
            Platform.runLater(() -> content.getChildren().set(1, patientTable(patients)));
        });
    }

    private void showAdminReports() {
        VBox content = new VBox(18, new ProgressIndicator());
        setContent("Reports & Analytics", "Comprehensive system insights and statistics", content);
        runAsync(null, () -> {
            Map<String, Object> summary = api.getObject("/api/admin/reports/summary/");
            List<Map<String, Object>> scans = api.getList("/api/scans/");
            Platform.runLater(() -> {
                HBox stats = new HBox(16,
                    statCard("Total Patients", Json.asString(summary.get("total_patients")), "blue"),
                    statCard("Active Doctors", Json.asString(summary.get("active_doctors")), "teal"),
                    statCard("X-Ray Scans", Json.asString(summary.get("xray_scans")), "purple"),
                    statCard("Needs Attention", Json.asString(summary.get("needs_attention")), "green")
                );
                content.getChildren().setAll(stats, scanTable(scans));
            });
        });
    }

    private VBox createDoctorForm() {
        VBox box = card();
        TextField username = input("Username");
        TextField email = input("Email Address");
        PasswordField password = passwordInput("Initial Password");
        TextField first = input("First Name");
        TextField last = input("Last Name");
        TextField specialist = input("Specialist");
        TextField phone = input("Phone Number");
        Button add = primaryButton("Add Doctor");
        add.setOnAction(e -> runAsync(null, () -> {
            api.postJson("/api/admin/doctors/", Map.of(
                "username", username.getText(),
                "email", email.getText(),
                "password", password.getText(),
                "first_name", first.getText(),
                "last_name", last.getText(),
                "specialization", specialist.getText(),
                "phone_number", phone.getText()
            ));
            Platform.runLater(this::showManageDoctors);
        }));
        box.getChildren().addAll(sectionTitle("Create Doctor"), twoCol(username, email), twoCol(password, specialist), twoCol(first, last), phone, add);
        return box;
    }

    private VBox createPatientForm() {
        VBox box = card();
        TextField username = input("Username");
        TextField email = input("Email Address");
        PasswordField password = passwordInput("Initial Password");
        TextField first = input("First Name");
        TextField last = input("Last Name");
        TextField age = input("Age");
        ComboBox<String> gender = new ComboBox<>(FXCollections.observableArrayList("Male", "Female", "Other"));
        gender.setPromptText("Gender");
        gender.getStyleClass().add("input");
        TextField phone = input("Phone Number");
        TextField condition = input("Primary Condition");
        Button add = primaryButton("Add Patient");
        add.setOnAction(e -> runAsync(null, () -> {
            Map<String, Object> body = new LinkedHashMap<>();
            body.put("username", username.getText());
            body.put("email", email.getText());
            body.put("password", password.getText());
            body.put("first_name", first.getText());
            body.put("last_name", last.getText());
            Integer parsedAge = parseInt(age.getText());
            if (parsedAge != null) {
                body.put("age", parsedAge);
            }
            body.put("gender", value(gender));
            body.put("phone_number", phone.getText());
            body.put("primary_condition", condition.getText());
            api.postJson("/api/admin/patients/", body);
            Platform.runLater(this::showManagePatients);
        }));
        box.getChildren().addAll(sectionTitle("Create Patient"), twoCol(username, email), twoCol(password, phone), twoCol(first, last), twoCol(age, gender), condition, add);
        return box;
    }

    private void showDoctorDashboard() {
        VBox content = new VBox(18);
        VBox search = card();
        TextField patientId = input("Enter Patient ID, name, email, or phone");
        Button button = primaryButton("Search");
        HBox row = new HBox(10, patientId, button);
        HBox.setHgrow(patientId, Priority.ALWAYS);
        VBox result = new VBox(12);
        button.setOnAction(e -> searchPatients(patientId.getText(), result));
        search.getChildren().addAll(sectionTitle("Search Patient"), muted("Enter patient ID to view medical records and history"), row, result);
        content.getChildren().addAll(search, quickActions("X-ray Analysis", this::showDoctorUpload, "View History", this::showDoctorHistory));
        setContent("Doctor Dashboard", "Welcome back, " + Json.asString(currentUser.get("first_name")), content);
    }

    private void searchPatients(String query, VBox result) {
        runAsync(null, () -> {
            List<Map<String, Object>> patients = api.getList("/api/doctor/patients/search/?q=" + ApiClient.urlEncode(query));
            Platform.runLater(() -> result.getChildren().setAll(patientTable(patients)));
        });
    }

    private void showDoctorUpload() {
        VBox content = card();
        content.setAlignment(Pos.CENTER);
        content.setMinHeight(420);
        TextField patientId = input("Patient ID, e.g. P001");
        Label fileLabel = muted("No X-ray image selected");
        final File[] selected = new File[1];
        Button choose = ghostButton("Choose X-ray Image");
        Button upload = primaryButton("Upload and Analyze");
        VBox result = new VBox(12);
        choose.setOnAction(e -> {
            FileChooser chooser = new FileChooser();
            chooser.getExtensionFilters().add(new FileChooser.ExtensionFilter("X-ray images", "*.png", "*.jpg", "*.jpeg", "*.dcm"));
            selected[0] = chooser.showOpenDialog(stage);
            if (selected[0] != null) {
                fileLabel.setText(selected[0].getName());
            }
        });
        upload.setOnAction(e -> {
            if (selected[0] == null) {
                showError("Please choose an X-ray image first.");
                return;
            }
            runAsync(null, () -> {
                Map<String, Object> scan = api.uploadXray(patientId.getText(), selected[0]);
                Platform.runLater(() -> result.getChildren().setAll(scanDetailCard(scan)));
            });
        });
        content.getChildren().addAll(sectionTitle("X-ray Analysis"), muted("AI-powered medical image analysis for accurate diagnostics"), patientId, choose, fileLabel, upload, result);
        setContent("X-ray Analysis", "Upload medical images and save results for a patient", content);
    }

    private void showDoctorHistory() {
        VBox content = new VBox(18, tableLoading());
        setContent("Patient Scan History", "View and manage all patient X-ray scans and reports", content);
        runAsync(null, () -> {
            List<Map<String, Object>> scans = api.getList("/api/scans/");
            Platform.runLater(() -> content.getChildren().set(0, scanTable(scans)));
        });
    }

    private void showPatientDashboard() {
        VBox content = new VBox(18);
        HBox stats = new HBox(16,
            statCard("Patient ID", Json.asString(currentUser.get("patient_id")), "blue"),
            statCard("Blood Type", Json.asString(currentUser.get("blood_type")), "green")
        );
        VBox info = profileInfoCard(false);
        content.getChildren().addAll(stats, info, sectionTitle("Recent Medical Scans"), tableLoading());
        setContent("Welcome back, " + Json.asString(currentUser.get("first_name")) + "!", "Here's an overview of your medical information", content);
        runAsync(null, () -> {
            List<Map<String, Object>> scans = api.getList("/api/scans/");
            Platform.runLater(() -> content.getChildren().set(3, scanTable(scans)));
        });
    }

    private void showPatientReports() {
        VBox content = new VBox(18, tableLoading());
        setContent("My Medical Reports", "View and download your complete medical history", content);
        runAsync(null, () -> {
            List<Map<String, Object>> scans = api.getList("/api/scans/");
            Platform.runLater(() -> content.getChildren().set(0, scanTable(scans)));
        });
    }

    private void showProfile() {
        setContent("My Information", "View and update your personal information", profileInfoCard(true));
    }

    private VBox profileInfoCard(boolean editable) {
        VBox box = card();
        TextField first = input("First Name");
        first.setText(Json.asString(currentUser.get("first_name")));
        TextField last = input("Last Name");
        last.setText(Json.asString(currentUser.get("last_name")));
        TextField email = input("Email");
        email.setText(Json.asString(currentUser.get("email")));
        TextField phone = input("Phone Number");
        phone.setText(Json.asString(currentUser.get("phone_number")));
        TextField blood = input("Blood Type");
        blood.setText(Json.asString(currentUser.get("blood_type")));
        TextField condition = input("Primary Condition");
        condition.setText(Json.asString(currentUser.get("primary_condition")));
        TextArea address = new TextArea(Json.asString(currentUser.get("address")));
        address.setPromptText("Address");
        address.getStyleClass().add("text-area-input");
        address.setPrefRowCount(3);
        Label pictureLabel = muted("No profile picture selected");
        final File[] profilePicture = new File[1];
        Button choosePicture = ghostButton("Choose Profile Picture");
        choosePicture.setVisible(editable);
        choosePicture.setManaged(editable);
        choosePicture.setOnAction(e -> {
            FileChooser chooser = new FileChooser();
            chooser.getExtensionFilters().add(new FileChooser.ExtensionFilter("Images", "*.png", "*.jpg", "*.jpeg"));
            profilePicture[0] = chooser.showOpenDialog(stage);
            if (profilePicture[0] != null) {
                pictureLabel.setText(profilePicture[0].getName());
            }
        });

        Button save = primaryButton("Save Changes");
        save.setVisible(editable);
        save.setManaged(editable);
        save.setOnAction(e -> runAsync(null, () -> {
            currentUser = api.patchMultipart("/api/profile/", Map.of(
                "first_name", first.getText(),
                "last_name", last.getText(),
                "email", email.getText(),
                "phone_number", phone.getText(),
                "blood_type", blood.getText(),
                "primary_condition", condition.getText(),
                "address", address.getText()
            ), "profile_picture", profilePicture[0]);
            Platform.runLater(() -> alert("Profile updated successfully."));
        }));

        Button password = ghostButton("Change Password");
        password.setVisible(editable);
        password.setManaged(editable);
        password.setOnAction(e -> showChangePasswordDialog());

        for (var node : List.of(first, last, email, phone, blood, condition, address)) {
            node.setDisable(!editable);
        }

        box.getChildren().addAll(sectionTitle("Personal Details"), twoCol(first, last), twoCol(email, phone), twoCol(blood, condition), address, choosePicture, pictureLabel, twoCol(save, password));
        return box;
    }

    private void showPasswordResetRequest() {
        javafx.scene.control.Dialog<Void> dialog = new javafx.scene.control.Dialog<>();
        dialog.setTitle("Reset Password");
        VBox box = new VBox(12);
        box.setPadding(new Insets(16));
        TextField email = input("Email Address");
        Label note = muted("A reset link will be sent through the configured SMTP email.");
        Button submit = primaryButton("Send Reset Link");
        box.getChildren().addAll(sectionTitle("Reset Password"), email, note, submit);
        dialog.getDialogPane().setContent(box);
        dialog.getDialogPane().getButtonTypes().add(javafx.scene.control.ButtonType.CLOSE);
        submit.setOnAction(e -> runAsync(null, () -> {
            api.postJson("/api/auth/password-reset/", Map.of("email", email.getText()));
            Platform.runLater(() -> {
                dialog.close();
                alert("If the email exists, a reset link has been sent.");
            });
        }));
        dialog.showAndWait();
    }

    private void showChangePasswordDialog() {
        javafx.scene.control.Dialog<Void> dialog = new javafx.scene.control.Dialog<>();
        dialog.setTitle("Change Password");
        VBox box = new VBox(12);
        box.setPadding(new Insets(16));
        PasswordField oldPassword = passwordInput("Current Password");
        PasswordField newPassword = passwordInput("New Password");
        Button submit = primaryButton("Change Password");
        box.getChildren().addAll(oldPassword, newPassword, submit);
        dialog.getDialogPane().setContent(box);
        dialog.getDialogPane().getButtonTypes().add(javafx.scene.control.ButtonType.CLOSE);
        submit.setOnAction(e -> runAsync(null, () -> {
            api.postJson("/api/profile/change-password/", Map.of(
                "old_password", oldPassword.getText(),
                "new_password", newPassword.getText()
            ));
            Platform.runLater(() -> {
                dialog.close();
                alert("Password changed. Please login again.");
                api.setToken(null);
                stage.getScene().setRoot(showLogin());
            });
        }));
        dialog.showAndWait();
    }

    private HBox quickActions(String first, Runnable firstAction, String second, Runnable secondAction) {
        Button a = ghostButton(first);
        Button b = ghostButton(second);
        a.setOnAction(e -> firstAction.run());
        b.setOnAction(e -> secondAction.run());
        HBox box = new HBox(14, a, b);
        a.setMaxWidth(Double.MAX_VALUE);
        b.setMaxWidth(Double.MAX_VALUE);
        HBox.setHgrow(a, Priority.ALWAYS);
        HBox.setHgrow(b, Priority.ALWAYS);
        return box;
    }

    private TableView<Map<String, Object>> doctorTable(List<Map<String, Object>> data) {
        TableView<Map<String, Object>> table = table(data);
        table.getColumns().add(col("Doctor ID", "doctor_id"));
        table.getColumns().add(col("Name", item -> fullName(item)));
        table.getColumns().add(col("Specialist", "specialization"));
        table.getColumns().add(col("Email", "email"));
        table.getColumns().add(col("Phone", "phone_number"));
        return table;
    }

    private TableView<Map<String, Object>> patientTable(List<Map<String, Object>> data) {
        TableView<Map<String, Object>> table = table(data);
        table.getColumns().add(col("Patient ID", "patient_id"));
        table.getColumns().add(col("Name", item -> fullName(item)));
        table.getColumns().add(col("Age", "age"));
        table.getColumns().add(col("Gender", "gender"));
        table.getColumns().add(col("Phone", "phone_number"));
        table.getColumns().add(col("Condition", "primary_condition"));
        return table;
    }

    private TableView<Map<String, Object>> scanTable(List<Map<String, Object>> data) {
        TableView<Map<String, Object>> table = table(data);
        table.getColumns().add(col("Scan ID", item -> "S" + Json.asString(item.get("id"))));
        table.getColumns().add(col("Patient", "patient_name"));
        table.getColumns().add(col("Patient ID", "patient_id"));
        table.getColumns().add(col("Date", item -> Json.asString(item.get("created_at")).replace("T", " ").split("\\.")[0]));
        table.getColumns().add(col("Type", "scan_type"));
        table.getColumns().add(col("Result", "prediction"));
        table.getColumns().add(col("Confidence", item -> percent(item.get("confidence"))));
        table.getColumns().add(col("Risk", "risk_level"));
        return table;
    }

    private TableView<Map<String, Object>> table(List<Map<String, Object>> data) {
        TableView<Map<String, Object>> table = new TableView<>(FXCollections.observableArrayList(data));
        table.getStyleClass().add("data-table");
        table.setColumnResizePolicy(TableView.CONSTRAINED_RESIZE_POLICY_ALL_COLUMNS);
        table.setMinHeight(280);
        return table;
    }

    private TableColumn<Map<String, Object>, String> col(String title, String key) {
        return col(title, item -> Json.asString(item.get(key)));
    }

    private TableColumn<Map<String, Object>, String> col(String title, CellValue value) {
        TableColumn<Map<String, Object>, String> column = new TableColumn<>(title);
        column.setCellValueFactory(data -> new SimpleStringProperty(value.get(data.getValue())));
        return column;
    }

    private Parent scanDetailCard(Map<String, Object> scan) {
        VBox box = card();
        Label prediction = sectionTitle("Result: " + Json.asString(scan.get("prediction")));
        Label confidence = muted("Confidence: " + percent(scan.get("confidence")) + "   Risk: " + Json.asString(scan.get("risk_level")));
        String heatmapUrl = Json.asString(scan.get("heatmap_image_url"));
        if (!heatmapUrl.isBlank()) {
            ImageView view = new ImageView(new Image(heatmapUrl, true));
            view.setFitHeight(260);
            view.setPreserveRatio(true);
            box.getChildren().addAll(prediction, confidence, view);
        } else {
            box.getChildren().addAll(prediction, confidence);
        }
        return box;
    }

    private VBox card() {
        VBox box = new VBox(14);
        box.getStyleClass().add("card");
        return box;
    }

    private VBox statCard(String label, String value, String tone) {
        VBox box = new VBox(8);
        box.getStyleClass().addAll("stat-card", tone);
        Label l = new Label(label);
        l.getStyleClass().add("stat-label");
        Label v = new Label(value == null || value.isBlank() ? "-" : value);
        v.getStyleClass().add("stat-value");
        box.getChildren().addAll(l, v);
        HBox.setHgrow(box, Priority.ALWAYS);
        return box;
    }

    private TextField input(String prompt) {
        TextField field = new TextField();
        field.setPromptText(prompt);
        field.getStyleClass().add("input");
        return field;
    }

    private PasswordField passwordInput(String prompt) {
        PasswordField field = new PasswordField();
        field.setPromptText(prompt);
        field.getStyleClass().add("input");
        return field;
    }

    private Button primaryButton(String text) {
        Button button = new Button(text);
        button.getStyleClass().add("primary-button");
        return button;
    }

    private Button ghostButton(String text) {
        Button button = new Button(text);
        button.getStyleClass().add("ghost-button");
        return button;
    }

    private Label sectionTitle(String text) {
        Label label = new Label(text);
        label.getStyleClass().add("section-title");
        return label;
    }

    private Label pageTitle(String text) {
        Label label = new Label(text);
        label.getStyleClass().add("page-title");
        return label;
    }

    private Label muted(String text) {
        Label label = new Label(text == null ? "" : text);
        label.getStyleClass().add("muted");
        return label;
    }

    private Parent tableLoading() {
        StackPane pane = new StackPane(new ProgressIndicator());
        pane.setMinHeight(260);
        return pane;
    }

    private HBox twoCol(Parent left, Parent right) {
        HBox box = new HBox(12, left, right);
        HBox.setHgrow(left, Priority.ALWAYS);
        HBox.setHgrow(right, Priority.ALWAYS);
        return box;
    }

    private String fullName(Map<String, Object> item) {
        String name = (Json.asString(item.get("first_name")) + " " + Json.asString(item.get("last_name"))).trim();
        return name.isBlank() ? Json.asString(item.get("username")) : name;
    }

    private String percent(Object value) {
        double number = Json.asDouble(value);
        if (number <= 1.0) {
            number *= 100.0;
        }
        return String.format("%.1f%%", number);
    }

    private String value(ComboBox<String> combo) {
        return combo.getValue() == null ? "" : combo.getValue();
    }

    private Integer parseInt(String text) {
        try {
            return Integer.parseInt(text);
        } catch (Exception e) {
            return null;
        }
    }

    private String capitalize(String text) {
        if (text == null || text.isBlank()) {
            return "";
        }
        return text.substring(0, 1).toUpperCase() + text.substring(1);
    }

    private void runAsync(Label message, ThrowingRunnable task) {
        if (message != null) {
            message.setText("");
        }
        Thread thread = new Thread(() -> {
            try {
                task.run();
            } catch (Exception ex) {
                Platform.runLater(() -> {
                    if (message != null) {
                        message.setText(ex.getMessage());
                    } else {
                        showError(ex.getMessage());
                    }
                });
            }
        });
        thread.setDaemon(true);
        thread.start();
    }

    private void showError(String message) {
        Alert alert = new Alert(Alert.AlertType.ERROR);
        alert.setTitle("MediCare");
        alert.setHeaderText("Something went wrong");
        alert.setContentText(message == null ? "Unknown error" : message);
        alert.showAndWait();
    }

    private void alert(String message) {
        Alert alert = new Alert(Alert.AlertType.INFORMATION);
        alert.setTitle("MediCare");
        alert.setHeaderText(null);
        alert.setContentText(message);
        alert.showAndWait();
    }

    @FunctionalInterface
    private interface ThrowingRunnable {
        void run() throws Exception;
    }

    @FunctionalInterface
    private interface CellValue {
        String get(Map<String, Object> item);
    }
}
