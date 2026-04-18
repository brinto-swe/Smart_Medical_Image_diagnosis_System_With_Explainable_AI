import java.io.File;
import java.awt.Desktop;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
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
import javafx.scene.control.ProgressBar;
import javafx.scene.control.ProgressIndicator;
import javafx.scene.control.ScrollPane;
import javafx.scene.control.Separator;
import javafx.scene.control.TableCell;
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
        File css = assetFile("src/styles.css");
        return css.exists() ? css.toURI().toString() : getClass().getResource("styles.css").toExternalForm();
    }

    private Parent showLogin() {
        VBox root = new VBox(24);
        root.getStyleClass().add("login-root");
        root.setAlignment(Pos.CENTER);

        ImageView logo = logoView(162);
        Label title = new Label("Medical Diagnosis Center");
        title.getStyleClass().add("login-title");
        Label subtitle = new Label("Select your role to access the dashboard");
        subtitle.getStyleClass().add("muted");

        HBox roleCards = new HBox(20,
                roleCard("Administrator", "Manage doctors, patients, and system reports"),
                roleCard("Doctor", "Search patients, analyze X-rays, and view history"),
                roleCard("Patient", "View medical reports and manage your information"));
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
                    "password", password.getText());
            Map<String, Object> response = api.postJson("/api/auth/signup/", body);
            api.setToken(Json.asString(response.get("token")));
            currentUser = Json.asObject(response.get("user"));
            Platform.runLater(this::showDashboardForCurrentUser);
        }));
        back.setOnAction(e -> stage.getScene().setRoot(showLogin()));

        form.getChildren().addAll(sectionTitle("Patient Signup"), username, email, firstName, lastName, password,
                submit, back, message);
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
        nav.setPrefWidth(188);

        ImageView logo = logoView(86);
        Label brand = new Label("MediCare");
        brand.getStyleClass().add("brand");
        Label portal = new Label(capitalize(role) + " Portal");
        portal.getStyleClass().add("portal");
        VBox brandText = new VBox(2, brand, portal);
        HBox header = new HBox(10, logo, brandText);
        header.setAlignment(Pos.CENTER_LEFT);
        header.setPadding(new Insets(16, 14, 16, 14));

        nav.getChildren().add(header);
        switch (role) {
            case "admin" -> nav.getChildren().addAll(
                    navButton("Dashboard", "dashboard.png", this::showAdminDashboard),
                    navButton("Manage Doctors", "user.png", this::showManageDoctors),
                    navButton("Manage Patients", "user.png", this::showManagePatients),
                    navButton("Reports", "reports.png", this::showAdminReports));
            case "doctor" -> nav.getChildren().addAll(
                    navButton("Dashboard", "dashboard.png", this::showDoctorDashboard),
                    navButton("X-ray Analysis", "scan.png", this::showDoctorUpload),
                    navButton("Patient History", "history.png", this::showDoctorHistory),
                    navButton("My Profile", "user.png", this::showProfile));
            default -> nav.getChildren().addAll(
                    navButton("My Dashboard", "dashboard.png", this::showPatientDashboard),
                    navButton("My Reports", "reports.png", this::showPatientReports),
                    navButton("My Information", "user.png", this::showProfile));
        }

        Region spacer = new Region();
        VBox.setVgrow(spacer, Priority.ALWAYS);
        VBox footer = profileFooter();
        Button logout = navButton("Logout", "logout.png", () -> {
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
        nav.getChildren().addAll(spacer, footer, logout);
        return nav;
    }

    private Button navButton(String text, Runnable action) {
        return navButton(text, null, action);
    }

    private Button navButton(String text, String iconFile, Runnable action) {
        Button button = new Button(text);
        button.getStyleClass().add("nav-button");
        button.setMaxWidth(Double.MAX_VALUE);
        if (iconFile != null) {
            button.setGraphic(iconGraphic(iconFile, 18));
        }
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
                stats.getChildren().set(0,
                        statCard("Total Doctors", Json.asString(summary.get("active_doctors")), "blue"));
                stats.getChildren().set(1,
                        statCard("Total Patients", Json.asString(summary.get("total_patients")), "teal"));
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
                        statCard("Needs Attention", Json.asString(summary.get("needs_attention")), "green"));
                content.getChildren().setAll(stats, reportSearchCard(), scanTable(scans));
            });
        });
    }

    private VBox reportSearchCard() {
        VBox box = card();
        TextField search = input("Search reports by Patient ID, name, or result");
        Button button = primaryButton("Search");
        HBox row = new HBox(10, search, button);
        HBox.setHgrow(search, Priority.ALWAYS);
        VBox results = new VBox(12);
        button.setOnAction(e -> runAsync(null, () -> {
            List<Map<String, Object>> scans = api.getList("/api/scans/?q=" + ApiClient.urlEncode(search.getText()));
            Platform.runLater(() -> results.getChildren().setAll(scanTable(scans)));
        }));
        box.getChildren().addAll(sectionTitle("Patient Report Printing"),
                muted("Search by patient ID, then preview or download from the Actions column."), row, results);
        return box;
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
                    "phone_number", phone.getText()));
            Platform.runLater(this::showManageDoctors);
        }));
        box.getChildren().addAll(sectionTitle("Create Doctor"), twoCol(username, email), twoCol(password, specialist),
                twoCol(first, last), phone, add);
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
        box.getChildren().addAll(sectionTitle("Create Patient"), twoCol(username, email), twoCol(password, phone),
                twoCol(first, last), twoCol(age, gender), condition, add);
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
        search.getChildren().addAll(sectionTitle("Search Patient"),
                muted("Enter patient ID to view medical records and history"), row, result);
        content.getChildren().addAll(search,
                quickActions("X-ray Analysis", this::showDoctorUpload, "View History", this::showDoctorHistory));
        setContent("Doctor Dashboard", "Welcome back, " + Json.asString(currentUser.get("first_name")), content);
    }

    private void searchPatients(String query, VBox result) {
        runAsync(null, () -> {
            List<Map<String, Object>> patients = api
                    .getList("/api/doctor/patients/search/?q=" + ApiClient.urlEncode(query));
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
            chooser.getExtensionFilters()
                    .add(new FileChooser.ExtensionFilter("X-ray images", "*.png", "*.jpg", "*.jpeg", "*.dcm"));
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
        content.getChildren().addAll(sectionTitle("X-ray Analysis"),
                muted("AI-powered medical image analysis for accurate diagnostics"), patientId, choose, fileLabel,
                upload, result);
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
                statCard("Blood Type", Json.asString(currentUser.get("blood_type")), "green"));
        VBox info = profileInfoCard(false);
        content.getChildren().addAll(stats, info, sectionTitle("Recent Medical Scans"), tableLoading());
        setContent("Welcome back, " + Json.asString(currentUser.get("first_name")) + "!",
                "Here's an overview of your medical information", content);
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
        TextField username = input("Username");
        username.setText(Json.asString(currentUser.get("username")));
        TextField email = input("Email");
        email.setText(Json.asString(currentUser.get("email")));
        TextField age = input("Age");
        age.setText(Json.asString(currentUser.get("age")));
        TextField phone = input("Phone Number");
        phone.setText(Json.asString(currentUser.get("phone_number")));
        TextField blood = input("Blood Type");
        blood.setText(Json.asString(currentUser.get("blood_type")));
        TextField specialization = input("Specialization");
        specialization.setText(Json.asString(currentUser.get("specialization")));
        TextField condition = input("Primary Condition");
        condition.setText(Json.asString(currentUser.get("primary_condition")));
        TextArea address = new TextArea(Json.asString(currentUser.get("address")));
        address.setPromptText("Address");
        address.getStyleClass().add("text-area-input");
        address.setPrefRowCount(3);
        Label pictureLabel = muted("No profile picture selected");
        final File[] profilePicture = new File[1];
        Label signatureLabel = muted("No electronic signature selected");
        final File[] signature = new File[1];
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
        Button chooseSignature = ghostButton("Choose Electronic Signature");
        boolean isDoctor = "doctor".equals(Json.asString(currentUser.get("role")));
        chooseSignature.setVisible(editable && isDoctor);
        chooseSignature.setManaged(editable && isDoctor);
        chooseSignature.setOnAction(e -> {
            FileChooser chooser = new FileChooser();
            chooser.getExtensionFilters()
                    .add(new FileChooser.ExtensionFilter("Signature images", "*.png", "*.jpg", "*.jpeg"));
            signature[0] = chooser.showOpenDialog(stage);
            if (signature[0] != null) {
                signatureLabel.setText(signature[0].getName());
            }
        });

        Button save = primaryButton("Save Changes");
        save.setVisible(editable);
        save.setManaged(editable);
        save.setOnAction(e -> runAsync(null, () -> {
            Map<String, Object> fields = new LinkedHashMap<>();
            fields.put("username", username.getText());
            fields.put("first_name", first.getText());
            fields.put("last_name", last.getText());
            fields.put("email", email.getText());
            fields.put("phone_number", phone.getText());
            Integer parsedAge = parseInt(age.getText());
            if (parsedAge != null) {
                fields.put("age", parsedAge);
            }
            fields.put("blood_type", blood.getText());
            fields.put("specialization", specialization.getText());
            fields.put("primary_condition", condition.getText());
            fields.put("address", address.getText());
            Map<String, File> files = new LinkedHashMap<>();
            files.put("profile_picture", profilePicture[0]);
            files.put("electronic_signature", signature[0]);
            currentUser = api.patchMultipart("/api/profile/", fields, files);
            Platform.runLater(() -> {
                alert("Profile updated successfully.");
                showDashboardForCurrentUser();
            });
        }));

        Button password = ghostButton("Change Password");
        password.setVisible(editable);
        password.setManaged(editable);
        password.setOnAction(e -> showChangePasswordDialog());

        for (var node : List.of(first, last, username, email, age, phone, blood, specialization, condition, address)) {
            node.setDisable(!editable);
        }

        List<Parent> rows = new ArrayList<>();
        rows.add(sectionTitle("Personal Details"));
        rows.add(twoCol(first, last));
        rows.add(twoCol(username, email));
        rows.add(twoCol(age, phone));
        rows.add(twoCol(blood, condition));
        if (isDoctor) {
            rows.add(specialization);
        }
        rows.add(address);
        rows.add(choosePicture);
        rows.add(pictureLabel);
        if (isDoctor) {
            rows.add(chooseSignature);
            rows.add(signatureLabel);
        }
        rows.add(twoCol(save, password));
        box.getChildren().addAll(rows);
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
                    "new_password", newPassword.getText()));
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
        table.getColumns().add(width(col("Scan ID", item -> "S" + Json.asString(item.get("id"))), 80));
        table.getColumns().add(width(col("Patient", "patient_name"), 185));
        table.getColumns().add(width(col("Patient ID", "patient_id"), 110));
        table.getColumns()
                .add(width(col("Date", item -> Json.asString(item.get("created_at")).replace("T", " ").split("\\.")[0]), 165));
        table.getColumns().add(width(col("Type", "scan_type"), 130));
        table.getColumns().add(width(resultCol(), 145));
        table.getColumns().add(width(confidenceCol(), 185));
        table.getColumns().add(width(col("Risk", "risk_level"), 95));
        table.getColumns().add(width(actionsCol(), 230));
        return table;
    }

    private TableView<Map<String, Object>> table(List<Map<String, Object>> data) {
        TableView<Map<String, Object>> table = new TableView<>(FXCollections.observableArrayList(data));
        table.getStyleClass().add("data-table");
        table.setColumnResizePolicy(TableView.CONSTRAINED_RESIZE_POLICY_ALL_COLUMNS);
        table.setMinHeight(280);
        table.setFixedCellSize(54);
        return table;
    }

    private TableColumn<Map<String, Object>, String> col(String title, String key) {
        return col(title, item -> Json.asString(item.get(key)));
    }

    private TableColumn<Map<String, Object>, String> col(String title, CellValue value) {
        TableColumn<Map<String, Object>, String> column = new TableColumn<>(title);
        column.setCellValueFactory(data -> new SimpleStringProperty(value.get(data.getValue())));
        column.setStyle("-fx-alignment: CENTER-LEFT;");
        return column;
    }

    private TableColumn<Map<String, Object>, String> width(TableColumn<Map<String, Object>, String> column, double value) {
        column.setMinWidth(value * 0.78);
        column.setPrefWidth(value);
        return column;
    }

    private TableColumn<Map<String, Object>, String> resultCol() {
        TableColumn<Map<String, Object>, String> column = col("Result", "prediction");
        column.setCellFactory(col -> new TableCell<>() {
            @Override
            protected void updateItem(String value, boolean empty) {
                super.updateItem(value, empty);
                if (empty || value == null) {
                    setGraphic(null);
                    setText(null);
                    return;
                }
                Label badge = new Label(value);
                badge.getStyleClass().addAll("badge",
                        "NORMAL".equalsIgnoreCase(value) ? "badge-normal" : "badge-alert");
                setGraphic(badge);
                setText(null);
            }
        });
        return column;
    }

    private TableColumn<Map<String, Object>, String> confidenceCol() {
        TableColumn<Map<String, Object>, String> column = new TableColumn<>("Confidence");
        column.setCellValueFactory(data -> new SimpleStringProperty(percent(data.getValue().get("confidence"))));
        column.setCellFactory(col -> new TableCell<>() {
            @Override
            protected void updateItem(String value, boolean empty) {
                super.updateItem(value, empty);
                if (empty || getTableRow() == null || getTableRow().getItem() == null) {
                    setGraphic(null);
                    setText(null);
                    return;
                }
                Map<String, Object> scan = getTableRow().getItem();
                double number = Json.asDouble(scan.get("confidence"));
                if (number <= 1.0) {
                    number *= 100.0;
                }
                ProgressBar bar = new ProgressBar(number / 100.0);
                bar.getStyleClass().add("confidence-bar");
                bar.setMinWidth(104);
                bar.setPrefWidth(114);
                Label label = new Label(String.format("%.1f%%", number));
                label.getStyleClass().add("confidence-label");
                label.setMinWidth(58);
                HBox box = new HBox(8, bar, label);
                box.setAlignment(Pos.CENTER_LEFT);
                setGraphic(box);
                setText(null);
            }
        });
        return column;
    }

    private TableColumn<Map<String, Object>, String> actionsCol() {
        TableColumn<Map<String, Object>, String> column = new TableColumn<>("Actions");
        column.setCellValueFactory(data -> new SimpleStringProperty(""));
        column.setCellFactory(col -> new TableCell<>() {
            @Override
            protected void updateItem(String value, boolean empty) {
                super.updateItem(value, empty);
                if (empty || getTableRow() == null || getTableRow().getItem() == null) {
                    setGraphic(null);
                    return;
                }
                Map<String, Object> scan = getTableRow().getItem();
                Button preview = compactButton("View", "eye.png");
                Button download = compactButton("Download", "download.png");
                preview.setOnAction(e -> previewReportForScan(scan));
                download.setOnAction(e -> downloadReportForScan(scan));
                HBox box = new HBox(8, preview, download);
                box.setAlignment(Pos.CENTER_LEFT);
                setGraphic(box);
            }
        });
        return column;
    }

    private Parent scanDetailCard(Map<String, Object> scan) {
        VBox box = card();
        Label prediction = sectionTitle("Result: " + Json.asString(scan.get("prediction")));
        Label confidence = muted(
                "Confidence: " + percent(scan.get("confidence")) + "   Risk: " + Json.asString(scan.get("risk_level")));
        Button generate = primaryButton("Generate PDF Report");
        generate.setGraphic(iconGraphic("print.png", 18));
        Button preview = ghostButton("Preview Report");
        preview.setGraphic(iconGraphic("eye.png", 18));
        Button download = ghostButton("Download Report");
        download.setGraphic(iconGraphic("download.png", 18));
        generate.setOnAction(e -> generateReportForScan(scan, false));
        preview.setOnAction(e -> previewReportForScan(scan));
        download.setOnAction(e -> downloadReportForScan(scan));
        HBox actions = new HBox(10, generate, preview, download);
        String heatmapUrl = Json.asString(scan.get("heatmap_image_url"));
        if (!heatmapUrl.isBlank()) {
            ImageView view = new ImageView(new Image(heatmapUrl, true));
            view.setFitHeight(260);
            view.setPreserveRatio(true);
            box.getChildren().addAll(prediction, confidence, view, actions);
        } else {
            box.getChildren().addAll(prediction, confidence, actions);
        }
        return box;
    }

    private Map<String, Object> ensureReport(Map<String, Object> scan) throws Exception {
        Object existing = scan.get("report_id");
        if (existing != null && !Json.asString(existing).isBlank()) {
            return Map.of("id", existing);
        }
        return api.postJson("/api/scans/" + Json.asString(scan.get("id")) + "/report/generate/", Map.of());
    }

    private void generateReportForScan(Map<String, Object> scan, boolean openAfter) {
        runAsync(null, () -> {
            Map<String, Object> report = api
                    .postJson("/api/scans/" + Json.asString(scan.get("id")) + "/report/generate/", Map.of());
            Platform.runLater(() -> {
                alert("PDF report generated and saved for this patient.");
                if (openAfter) {
                    openReport(Json.asString(report.get("id")), false, null);
                }
            });
        });
    }

    private void previewReportForScan(Map<String, Object> scan) {
        runAsync(null, () -> {
            Map<String, Object> report = ensureReport(scan);
            String reportId = Json.asString(report.get("id"));
            File pdf = api.downloadToTempFile("/api/reports/" + reportId + "/preview/", "medical-report-", ".pdf");
            Platform.runLater(() -> openLocalFile(pdf));
        });
    }

    private void downloadReportForScan(Map<String, Object> scan) {
        FileChooser chooser = new FileChooser();
        chooser.setTitle("Save Medical Report");
        chooser.setInitialFileName("medical_report_" + Json.asString(scan.get("patient_id")) + "_S"
                + Json.asString(scan.get("id")) + ".pdf");
        chooser.getExtensionFilters().add(new FileChooser.ExtensionFilter("PDF files", "*.pdf"));
        File target = chooser.showSaveDialog(stage);
        if (target == null) {
            return;
        }
        runAsync(null, () -> {
            Map<String, Object> report = ensureReport(scan);
            api.downloadToFile("/api/reports/" + Json.asString(report.get("id")) + "/download/", target);
            Platform.runLater(() -> alert("Report downloaded successfully."));
        });
    }

    private void openReport(String reportId, boolean download, File target) {
        runAsync(null, () -> {
            if (download && target != null) {
                api.downloadToFile("/api/reports/" + reportId + "/download/", target);
            } else {
                File pdf = api.downloadToTempFile("/api/reports/" + reportId + "/preview/", "medical-report-", ".pdf");
                Platform.runLater(() -> openLocalFile(pdf));
            }
        });
    }

    private void openLocalFile(File file) {
        try {
            if (Desktop.isDesktopSupported()) {
                Desktop.getDesktop().open(file);
            } else {
                alert("Report saved at: " + file.getAbsolutePath());
            }
        } catch (Exception ex) {
            showError(ex.getMessage());
        }
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

    private Button compactButton(String text) {
        return compactButton(text, null);
    }

    private Button compactButton(String text, String iconFile) {
        Button button = new Button(text);
        button.getStyleClass().add("compact-button");
        if (iconFile != null) {
            button.setGraphic(iconGraphic(iconFile, 18));
        }
        return button;
    }

    private ImageView iconGraphic(String fileName, double size) {
        File file = assetFile("icons/" + fileName);
        ImageView view = new ImageView();
        if (file.exists()) {
            view.setImage(new Image(file.toURI().toString(), true));
        }
        view.setFitWidth(size);
        view.setFitHeight(size);
        view.setPreserveRatio(true);
        view.setSmooth(true);
        view.setCache(true);
        return view;
    }

    private ImageView logoView(double size) {
        File logo = assetFile("icons/logo.png");
        ImageView view = new ImageView();
        if (logo.exists()) {
            view.setImage(new Image(logo.toURI().toString(), true));
        }
        view.setFitWidth(size);
        view.setFitHeight(size);
        view.setPreserveRatio(true);
        view.setSmooth(true);
        view.setCache(true);
        return view;
    }

    private File assetFile(String relativePath) {
        File cwd = new File(System.getProperty("user.dir"));
        List<File> candidates = List.of(
                new File(cwd, relativePath),
                new File(cwd, "frontend/MedicalDiagnosisGUI/" + relativePath),
                new File("C:/Users/mozad/Desktop/SmartMedicalProject/frontend/MedicalDiagnosisGUI/" + relativePath));
        for (File file : candidates) {
            if (file.exists()) {
                return file;
            }
        }
        return candidates.get(0);
    }

    private VBox profileFooter() {
        VBox box = new VBox(8);
        box.getStyleClass().add("profile-footer");
        box.setOnMouseClicked(e -> showProfile());
        HBox row = new HBox(10);
        row.setAlignment(Pos.CENTER_LEFT);

        String pictureUrl = Json.asString(currentUser.get("profile_picture_url"));
        if (!pictureUrl.isBlank()) {
            ImageView avatar = new ImageView(new Image(pictureUrl, true));
            avatar.setFitWidth(34);
            avatar.setFitHeight(34);
            avatar.setPreserveRatio(true);
            row.getChildren().add(avatar);
        } else {
            Label avatar = new Label(userInitial());
            avatar.getStyleClass().add("avatar");
            row.getChildren().add(avatar);
        }

        Label name = new Label(displayName());
        name.getStyleClass().add("profile-name");
        Label username = new Label("@" + Json.asString(currentUser.get("username")));
        username.getStyleClass().add("profile-username");
        row.getChildren().add(new VBox(2, name, username));
        box.getChildren().add(row);
        return box;
    }

    private String displayName() {
        String name = fullName(currentUser);
        return name.isBlank() ? Json.asString(currentUser.get("username")) : name;
    }

    private String userInitial() {
        String name = displayName();
        return name.isBlank() ? "U" : name.substring(0, 1).toUpperCase();
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
