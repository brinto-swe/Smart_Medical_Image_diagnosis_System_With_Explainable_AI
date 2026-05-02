import java.io.File;
import java.awt.Desktop;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import javafx.application.Application;
import javafx.application.Platform;
import javafx.beans.property.SimpleStringProperty;
import javafx.collections.ObservableList;
import javafx.collections.FXCollections;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.chart.BarChart;
import javafx.scene.chart.CategoryAxis;
import javafx.scene.chart.LineChart;
import javafx.scene.chart.NumberAxis;
import javafx.scene.chart.PieChart;
import javafx.scene.chart.XYChart;
import javafx.scene.control.Alert;
import javafx.scene.control.Button;
import javafx.scene.control.ComboBox;
import javafx.scene.control.DatePicker;
import javafx.scene.control.Dialog;
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
    private String selectedDiagnosisPatientId;

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
        VBox root = new VBox(28);
        root.getStyleClass().add("login-root");
        root.setAlignment(Pos.CENTER);

        ImageView logo = logoView(210);
        Label title = new Label("Medical Diagnosis Center");
        title.getStyleClass().add("login-title");
        Label subtitle = new Label("Sign in to access your dashboard");
        subtitle.getStyleClass().add("muted");
        VBox hero = new VBox(12, logo, title, subtitle);
        hero.setAlignment(Pos.CENTER);

        VBox form = card();
        form.getStyleClass().add("login-card");
        form.setMaxWidth(500);
        form.setAlignment(Pos.CENTER);
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

        Label formTitle = sectionTitle("Login");
        formTitle.getStyleClass().add("login-form-title");
        form.getChildren().addAll(formTitle, username, password, login, signup, forgot, message);
        root.getChildren().addAll(hero, form);
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

        ImageView logo = logoView(108);
        Label brand = new Label("MediCare");
        brand.getStyleClass().add("brand");
        Label portal = new Label(capitalize(role) + " Portal");
        portal.getStyleClass().add("portal");
        VBox header = new VBox(8, logo, brand, portal);
        header.setAlignment(Pos.CENTER_LEFT);
        header.setPadding(new Insets(16, 14, 16, 14));

        nav.getChildren().add(header);
        switch (role) {
            case "admin" -> nav.getChildren().addAll(
                    navButton("Dashboard", "dashboard.png", this::showAdminDashboard),
                    navButton("Manage Doctors", "user.png", this::showManageDoctors),
                    navButton("Manage Patients", "user.png", this::showManagePatients),
                    navButton("Assign Doctor", "history.png", this::showAssignDoctor),
                    navButton("Reports", "reports.png", this::showAdminReports));
            case "doctor" -> nav.getChildren().addAll(
                    navButton("Dashboard", "dashboard.png", this::showDoctorDashboard),
                    navButton("Assigned Patients", "user.png", this::showAssignedPatients),
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
            button.setGraphic(iconGraphic(iconFile, 20));
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
        ComboBox<String> period = new ComboBox<>(FXCollections.observableArrayList("Monthly", "Weekly", "Daily"));
        period.getStyleClass().add("input");
        period.setValue("Monthly");
        HBox controls = new HBox(12, sectionTitle("Medical Analytics"), period);
        controls.setAlignment(Pos.CENTER_LEFT);

        HBox stats = new HBox(16,
                statCard("Total Doctors", "-", "blue"),
                statCard("Total Patients", "-", "teal"),
                statCard("Assignments", "-", "purple"),
                statCard("X-Ray Scans", "-", "green"));

        GridPane charts = new GridPane();
        charts.setHgap(18);
        charts.setVgap(18);
        charts.add(chartPlaceholder("Patient Growth"), 0, 0);
        charts.add(chartPlaceholder("Doctor Assignment Split"), 1, 0);
        charts.add(chartPlaceholder("Scan Volume"), 0, 1);
        charts.add(chartPlaceholder("Disease Distribution"), 1, 1);

        content.getChildren().addAll(controls, stats, charts, sectionTitle("Recently Added Doctors"), doctorTable(List.of()));
        setContent("Admin Dashboard", "Manage your healthcare system", content);

        Runnable load = () -> runAsync(null, () -> {
            String selected = Json.asString(period.getValue()).toLowerCase();
            Map<String, Object> summary = api.getObject("/api/admin/reports/summary/?period=" + ApiClient.urlEncode(selected));
            List<Map<String, Object>> doctors = api.getList("/api/admin/doctors/");
            Platform.runLater(() -> {
                stats.getChildren().set(0,
                        statCard("Total Doctors", Json.asString(summary.get("active_doctors")), "blue"));
                stats.getChildren().set(1,
                        statCard("Total Patients", Json.asString(summary.get("total_patients")), "teal"));
                stats.getChildren().set(2,
                        statCard("Assignments", Json.asString(summary.get("total_assignments")), "purple"));
                stats.getChildren().set(3,
                        statCard("X-Ray Scans", Json.asString(summary.get("xray_scans")), "green"));
                setChartGrid(charts,
                        chartCard("Patient Growth",
                                lineChart("Patients Joined", Json.asObject(summary.get("patient_growth")), "blue")),
                        chartCard("Doctor Assignment Split",
                                doctorAssignmentChart(Json.asListOfObjects(summary.get("doctor_assignment_distribution")))),
                        chartCard("Scan Volume",
                                barChart("Scans", Json.asObject(summary.get("scan_volume")), "teal")),
                        chartCard("Disease Distribution",
                                horizontalBarChart(Json.asListOfObjects(summary.get("disease_distribution")))));
                content.getChildren().set(4, doctorTable(doctors));
            });
        });
        period.setOnAction(e -> load.run());
        load.run();
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

    private void showAssignDoctor() {
        VBox content = new VBox(18);
        VBox searchCard = card();
        TextField patientSearch = input("Enter Patient ID, e.g. P001");
        Button search = primaryButton("Search Patient");
        HBox searchRow = new HBox(10, patientSearch, search);
        HBox.setHgrow(patientSearch, Priority.ALWAYS);
        VBox resultBox = new VBox(12);
        searchCard.getChildren().addAll(
                sectionTitle("Assign Doctor"),
                muted("Search the patient, choose a doctor, select date and time, then assign the case."),
                searchRow,
                resultBox);
        content.getChildren().add(searchCard);
        setContent("Assign Doctor", "Schedule patients with the right doctor", content);

        Runnable searchAction = () -> runAsync(null, () -> {
            List<Map<String, Object>> patients = api.getList("/api/admin/patients/?q=" + ApiClient.urlEncode(patientSearch.getText()));
            List<Map<String, Object>> doctors = api.getList("/api/admin/doctors/");
            Platform.runLater(() -> {
                if (patients.isEmpty()) {
                    resultBox.getChildren().setAll(muted("No patient found for that ID."));
                    return;
                }
                resultBox.getChildren().setAll(assignDoctorCard(patients.get(0), doctors));
            });
        });
        search.setOnAction(e -> searchAction.run());
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
                quickActions("Assigned Patients", this::showAssignedPatients, "X-ray Analysis", this::showDoctorUpload));
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
        if (selectedDiagnosisPatientId != null && !selectedDiagnosisPatientId.isBlank()) {
            patientId.setText(selectedDiagnosisPatientId);
        }
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
                Platform.runLater(() -> {
                    selectedDiagnosisPatientId = null;
                    result.getChildren().setAll(scanDetailCard(scan));
                });
            });
        });
        content.getChildren().addAll(sectionTitle("X-ray Analysis"),
                muted("AI-powered medical image analysis for accurate diagnostics"), patientId, choose, fileLabel,
                upload, result);
        setContent("X-ray Analysis", "Upload medical images and save results for a patient", content);
    }

    private void showAssignedPatients() {
        VBox content = new VBox(18);
        DatePicker datePicker = new DatePicker(LocalDate.now());
        datePicker.getStyleClass().add("input");
        TextField search = input("Search by Patient ID or name");
        Button refresh = primaryButton("Load");
        HBox filters = new HBox(10, search, datePicker, refresh);
        HBox.setHgrow(search, Priority.ALWAYS);
        content.getChildren().addAll(filters, tableLoading());
        setContent("Assigned Patients", "View your scheduled patients and start diagnosis directly", content);

        Runnable load = () -> runAsync(null, () -> {
            String path = "/api/doctor/assignments/?date=" + ApiClient.urlEncode(datePicker.getValue().toString())
                    + "&q=" + ApiClient.urlEncode(search.getText());
            List<Map<String, Object>> assignments = api.getList(path);
            Platform.runLater(() -> content.getChildren().set(1, assignmentTable(assignments)));
        });
        refresh.setOnAction(e -> load.run());
        datePicker.setOnAction(e -> load.run());
        load.run();
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

    private VBox assignDoctorCard(Map<String, Object> patient, List<Map<String, Object>> doctors) {
        VBox box = card();
        Label patientInfo = sectionTitle(fullName(patient) + " (" + Json.asString(patient.get("patient_id")) + ")");
        Label patientMeta = muted("Phone: " + Json.asString(patient.get("phone_number")) + "   Condition: "
                + Json.asString(patient.get("primary_condition")));

        ComboBox<String> doctorSelect = new ComboBox<>();
        doctorSelect.getStyleClass().add("input");
        Map<String, String> doctorLookup = new LinkedHashMap<>();
        for (Map<String, Object> doctor : doctors) {
            String doctorId = Json.asString(doctor.get("doctor_id"));
            String label = doctorId.isBlank() ? fullName(doctor) : fullName(doctor) + " - " + doctorId;
            doctorLookup.put(label, Json.asString(doctor.get("doctor_id")));
        }
        doctorSelect.setItems(FXCollections.observableArrayList(doctorLookup.keySet()));
        doctorSelect.setPromptText("Select Doctor");
        if (!doctorSelect.getItems().isEmpty()) {
            doctorSelect.setValue(doctorSelect.getItems().get(0));
        }

        DatePicker datePicker = new DatePicker(LocalDate.now());
        datePicker.getStyleClass().add("input");
        ComboBox<String> timeSelect = new ComboBox<>(FXCollections.observableArrayList(timeOptions()));
        timeSelect.getStyleClass().add("input");
        timeSelect.setPromptText("Select Time");
        timeSelect.setValue("09:00 AM");
        TextField notes = input("Notes (optional)");
        Button assign = primaryButton("Assign Doctor");
        assign.setOnAction(e -> runAsync(null, () -> {
            String doctorId = doctorLookup.get(doctorSelect.getValue());
            LocalTime time = LocalTime.parse(timeSelect.getValue(), DateTimeFormatter.ofPattern("hh:mm a"));
            LocalDateTime scheduled = LocalDateTime.of(datePicker.getValue(), time);
            api.postJson("/api/admin/assignments/", Map.of(
                    "patient_id", Json.asString(patient.get("patient_id")),
                    "doctor_id", doctorId,
                    "scheduled_at", scheduled.toString(),
                    "notes", notes.getText()));
            Platform.runLater(() -> {
                alert("Doctor assigned successfully.");
                showAssignDoctor();
            });
        }));

        box.getChildren().addAll(
                patientInfo,
                patientMeta,
                twoCol(doctorSelect, datePicker),
                twoCol(timeSelect, notes),
                assign);
        return box;
    }

    private List<String> timeOptions() {
        List<String> options = new ArrayList<>();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("hh:mm a");
        for (int hour = 8; hour <= 18; hour++) {
            options.add(LocalTime.of(hour, 0).format(formatter));
            if (hour < 18) {
                options.add(LocalTime.of(hour, 30).format(formatter));
            }
        }
        return options;
    }

    private VBox chartPlaceholder(String title) {
        VBox box = card();
        box.getStyleClass().add("chart-card");
        box.setMinHeight(320);
        box.getChildren().addAll(sectionTitle(title), muted("Loading analytics..."));
        return box;
    }

    private VBox chartCard(String title, Parent chart) {
        VBox box = card();
        box.getStyleClass().add("chart-card");
        box.setMinHeight(320);
        box.getChildren().addAll(sectionTitle(title), chart);
        VBox.setVgrow(chart, Priority.ALWAYS);
        return box;
    }

    private void setChartGrid(GridPane grid, Parent topLeft, Parent topRight, Parent bottomLeft, Parent bottomRight) {
        grid.getChildren().clear();
        grid.add(topLeft, 0, 0);
        grid.add(topRight, 1, 0);
        grid.add(bottomLeft, 0, 1);
        grid.add(bottomRight, 1, 1);
        GridPane.setHgrow(topLeft, Priority.ALWAYS);
        GridPane.setHgrow(topRight, Priority.ALWAYS);
        GridPane.setHgrow(bottomLeft, Priority.ALWAYS);
        GridPane.setHgrow(bottomRight, Priority.ALWAYS);
    }

    private Parent lineChart(String seriesName, Map<String, Object> chartData, String colorClass) {
        CategoryAxis xAxis = new CategoryAxis();
        NumberAxis yAxis = new NumberAxis();
        LineChart<String, Number> chart = new LineChart<>(xAxis, yAxis);
        chart.setLegendVisible(false);
        chart.setAnimated(false);
        chart.setCreateSymbols(true);
        chart.setMinHeight(260);
        chart.getStyleClass().addAll("analytics-chart", colorClass);
        XYChart.Series<String, Number> series = new XYChart.Series<>();
        series.setName(seriesName);
        for (int i = 0; i < Json.asList(chartData.get("labels")).size(); i++) {
            String label = Json.asString(Json.asList(chartData.get("labels")).get(i));
            Number value = Json.asDouble(Json.asList(chartData.get("values")).get(i));
            series.getData().add(new XYChart.Data<>(label, value));
        }
        chart.getData().add(series);
        return chart;
    }

    private Parent barChart(String seriesName, Map<String, Object> chartData, String colorClass) {
        CategoryAxis xAxis = new CategoryAxis();
        NumberAxis yAxis = new NumberAxis();
        BarChart<String, Number> chart = new BarChart<>(xAxis, yAxis);
        chart.setLegendVisible(false);
        chart.setAnimated(false);
        chart.setMinHeight(260);
        chart.getStyleClass().addAll("analytics-chart", colorClass);
        XYChart.Series<String, Number> series = new XYChart.Series<>();
        series.setName(seriesName);
        for (int i = 0; i < Json.asList(chartData.get("labels")).size(); i++) {
            String label = Json.asString(Json.asList(chartData.get("labels")).get(i));
            Number value = Json.asDouble(Json.asList(chartData.get("values")).get(i));
            series.getData().add(new XYChart.Data<>(label, value));
        }
        chart.getData().add(series);
        return chart;
    }

    private Parent horizontalBarChart(List<Map<String, Object>> rows) {
        NumberAxis xAxis = new NumberAxis();
        CategoryAxis yAxis = new CategoryAxis();
        BarChart<Number, String> chart = new BarChart<>(xAxis, yAxis);
        chart.setLegendVisible(false);
        chart.setAnimated(false);
        chart.setMinHeight(260);
        chart.getStyleClass().addAll("analytics-chart", "green");
        XYChart.Series<Number, String> series = new XYChart.Series<>();
        for (Map<String, Object> row : rows) {
            series.getData().add(new XYChart.Data<>(Json.asDouble(row.get("value")), Json.asString(row.get("label"))));
        }
        chart.getData().add(series);
        return chart;
    }

    private Parent doctorAssignmentChart(List<Map<String, Object>> rows) {
        ObservableList<PieChart.Data> pieData = FXCollections.observableArrayList();
        for (Map<String, Object> row : rows) {
            pieData.add(new PieChart.Data(
                    Json.asString(row.get("doctor_name")) + " (" + Json.asString(row.get("total")) + ")",
                    Json.asDouble(row.get("total"))));
        }
        PieChart chart = new PieChart(pieData);
        chart.setLegendVisible(true);
        chart.setLabelsVisible(true);
        chart.setMinHeight(260);
        chart.getStyleClass().add("analytics-chart");
        return chart;
    }

    private TableView<Map<String, Object>> doctorTable(List<Map<String, Object>> data) {
        TableView<Map<String, Object>> table = table(data);
        table.getColumns().add(width(col("Doctor ID", "doctor_id"), 100));
        table.getColumns().add(width(col("Name", item -> fullName(item)), 180));
        table.getColumns().add(width(col("Specialist", "specialization"), 140));
        table.getColumns().add(width(col("Email", "email"), 200));
        table.getColumns().add(width(col("Phone", "phone_number"), 135));
        table.getColumns().add(width(adminUserActionsCol("doctor"), 250));
        return table;
    }

    private TableView<Map<String, Object>> patientTable(List<Map<String, Object>> data) {
        TableView<Map<String, Object>> table = table(data);
        table.getColumns().add(width(col("Patient ID", "patient_id"), 100));
        table.getColumns().add(width(col("Name", item -> fullName(item)), 180));
        table.getColumns().add(width(col("Age", "age"), 70));
        table.getColumns().add(width(col("Gender", "gender"), 90));
        table.getColumns().add(width(col("Phone", "phone_number"), 135));
        table.getColumns().add(width(col("Condition", "primary_condition"), 150));
        table.getColumns().add(width(adminUserActionsCol("patient"), 250));
        return table;
    }

    private TableView<Map<String, Object>> assignmentTable(List<Map<String, Object>> data) {
        TableView<Map<String, Object>> table = table(data);
        table.getColumns().add(width(col("Patient", "patient_name"), 190));
        table.getColumns().add(width(col("Patient ID", "patient_id"), 110));
        table.getColumns().add(width(col("Doctor", "doctor_name"), 190));
        table.getColumns().add(width(col("Doctor ID", "doctor_id"), 105));
        table.getColumns().add(width(col("Date & Time", item -> formatApiDate(Json.asString(item.get("scheduled_at")))), 195));
        table.getColumns().add(width(col("Notes", "notes"), 190));
        if (isDoctor()) {
            table.getColumns().add(width(assignmentActionsCol(), 170));
        }
        return table;
    }

    private TableView<Map<String, Object>> scanTable(List<Map<String, Object>> data) {
        TableView<Map<String, Object>> table = table(data);
        table.getColumns().add(width(col("Scan ID", item -> "S" + Json.asString(item.get("id"))), 80));
        table.getColumns().add(width(col("Patient", "patient_name"), 185));
        table.getColumns().add(width(col("Patient ID", "patient_id"), 110));
        table.getColumns()
                .add(width(col("Date", item -> formatApiDate(Json.asString(item.get("created_at")))), 165));
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
                if (isAdmin()) {
                    Button edit = compactButton("Edit", "edit.png");
                    Button delete = compactButton("Delete", "delete.png");
                    edit.setOnAction(e -> editReportForScan(scan));
                    delete.setOnAction(e -> deleteReportForScan(scan));
                    box.getChildren().addAll(edit, delete);
                }
                box.setAlignment(Pos.CENTER_LEFT);
                setGraphic(box);
            }
        });
        return column;
    }

    private TableColumn<Map<String, Object>, String> adminUserActionsCol(String type) {
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
                Map<String, Object> item = getTableRow().getItem();
                Button view = compactButton("View", "eye.png");
                Button edit = compactButton("Edit", "edit.png");
                Button delete = compactButton("Delete", "delete.png");
                view.setOnAction(e -> showAdminUserViewDialog(type, item));
                edit.setOnAction(e -> showAdminUserEditDialog(type, item));
                delete.setOnAction(e -> deleteAdminUser(type, item));
                HBox box = new HBox(8, view, edit, delete);
                box.setAlignment(Pos.CENTER_LEFT);
                setGraphic(box);
            }
        });
        return column;
    }

    private TableColumn<Map<String, Object>, String> assignmentActionsCol() {
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
                Map<String, Object> assignment = getTableRow().getItem();
                Button start = compactButton("Start Diagnosis", "scan.png");
                start.setOnAction(e -> {
                    selectedDiagnosisPatientId = Json.asString(assignment.get("patient_id"));
                    showDoctorUpload();
                });
                HBox box = new HBox(start);
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
        Button preview = ghostButton("Preview Report");
        preview.setGraphic(iconGraphic("eye.png", 20));
        Button download = ghostButton("Download Report");
        download.setGraphic(iconGraphic("download.png", 20));
        preview.setOnAction(e -> previewReportForScan(scan));
        download.setOnAction(e -> downloadReportForScan(scan));
        HBox actions = new HBox(10);
        if (isAdmin() || isDoctor()) {
            Button generate = primaryButton("Generate PDF Report");
            generate.setGraphic(iconGraphic("print.png", 22));
            generate.setOnAction(e -> generateReportForScan(scan, false));
            actions.getChildren().add(generate);
        }
        actions.getChildren().addAll(preview, download);
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

    private void showAdminUserViewDialog(String type, Map<String, Object> item) {
        Dialog<Void> dialog = new Dialog<>();
        dialog.setTitle("View " + capitalize(type));
        VBox box = card();
        box.getChildren().addAll(
                sectionTitle(capitalize(type) + " Details"),
                muted(type.equals("doctor") ? "Doctor ID: " + Json.asString(item.get("doctor_id"))
                        : "Patient ID: " + Json.asString(item.get("patient_id"))),
                muted("Name: " + fullName(item)),
                muted("Username: " + Json.asString(item.get("username"))),
                muted("Email: " + Json.asString(item.get("email"))),
                muted("Phone: " + Json.asString(item.get("phone_number"))),
                muted("Age: " + Json.asString(item.get("age"))),
                muted("Gender: " + Json.asString(item.get("gender"))),
                muted("Specialization: " + Json.asString(item.get("specialization"))),
                muted("Condition: " + Json.asString(item.get("primary_condition"))));
        dialog.getDialogPane().setContent(box);
        dialog.getDialogPane().getButtonTypes().add(javafx.scene.control.ButtonType.CLOSE);
        dialog.showAndWait();
    }

    private void showAdminUserEditDialog(String type, Map<String, Object> item) {
        Dialog<Void> dialog = new Dialog<>();
        dialog.setTitle("Edit " + capitalize(type));
        VBox box = new VBox(12);
        box.setPadding(new Insets(16));
        TextField username = input("Username");
        username.setText(Json.asString(item.get("username")));
        TextField email = input("Email");
        email.setText(Json.asString(item.get("email")));
        TextField first = input("First Name");
        first.setText(Json.asString(item.get("first_name")));
        TextField last = input("Last Name");
        last.setText(Json.asString(item.get("last_name")));
        TextField phone = input("Phone Number");
        phone.setText(Json.asString(item.get("phone_number")));
        TextField age = input("Age");
        age.setText(Json.asString(item.get("age")));
        TextField gender = input("Gender");
        gender.setText(Json.asString(item.get("gender")));
        TextField specialization = input("Specialization");
        specialization.setText(Json.asString(item.get("specialization")));
        TextField condition = input("Primary Condition");
        condition.setText(Json.asString(item.get("primary_condition")));
        Button save = primaryButton("Save Changes");
        box.getChildren().addAll(username, email, first, last, phone, age, gender);
        if ("doctor".equals(type)) {
            box.getChildren().add(specialization);
        } else {
            box.getChildren().add(condition);
        }
        box.getChildren().add(save);
        dialog.getDialogPane().setContent(box);
        dialog.getDialogPane().getButtonTypes().add(javafx.scene.control.ButtonType.CLOSE);
        save.setOnAction(e -> runAsync(null, () -> {
            Map<String, Object> body = new LinkedHashMap<>();
            body.put("username", username.getText());
            body.put("email", email.getText());
            body.put("first_name", first.getText());
            body.put("last_name", last.getText());
            body.put("phone_number", phone.getText());
            Integer parsedAge = parseInt(age.getText());
            if (parsedAge != null) {
                body.put("age", parsedAge);
            }
            body.put("gender", gender.getText());
            if ("doctor".equals(type)) {
                body.put("specialization", specialization.getText());
                api.patchJson("/api/admin/doctors/" + Json.asString(item.get("id")) + "/", body);
            } else {
                body.put("primary_condition", condition.getText());
                api.patchJson("/api/admin/patients/" + Json.asString(item.get("id")) + "/", body);
            }
            Platform.runLater(() -> {
                dialog.close();
                if ("doctor".equals(type)) {
                    showManageDoctors();
                } else {
                    showManagePatients();
                }
            });
        }));
        dialog.showAndWait();
    }

    private void deleteAdminUser(String type, Map<String, Object> item) {
        if (!confirm("Delete " + type, "Are you sure you want to delete this " + type + "?")) {
            return;
        }
        runAsync(null, () -> {
            if ("doctor".equals(type)) {
                api.delete("/api/admin/doctors/" + Json.asString(item.get("id")) + "/");
                Platform.runLater(this::showManageDoctors);
            } else {
                api.delete("/api/admin/patients/" + Json.asString(item.get("id")) + "/");
                Platform.runLater(this::showManagePatients);
            }
        });
    }

    private void editReportForScan(Map<String, Object> scan) {
        runAsync(null, () -> {
            Map<String, Object> report = ensureReport(scan);
            String reportId = Json.asString(report.get("id"));
            api.patchJson("/api/admin/reports/" + reportId + "/", Map.of("regenerate_pdf", true));
            Platform.runLater(() -> alert("Report updated successfully."));
        });
    }

    private void deleteReportForScan(Map<String, Object> scan) {
        if (!confirm("Delete report", "Are you sure you want to delete this report?")) {
            return;
        }
        Object existing = scan.get("report_id");
        if (existing == null || Json.asString(existing).isBlank()) {
            alert("No saved report exists for this scan yet.");
            return;
        }
        runAsync(null, () -> {
            api.delete("/api/admin/reports/" + Json.asString(existing) + "/");
            Platform.runLater(() -> {
                alert("Report deleted successfully.");
                showAdminReports();
            });
        });
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
            button.setGraphic(iconGraphic(iconFile, 20));
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

    private String currentRole() {
        return Json.asString(currentUser.get("role"));
    }

    private boolean isAdmin() {
        return "admin".equalsIgnoreCase(currentRole());
    }

    private boolean isDoctor() {
        return "doctor".equalsIgnoreCase(currentRole());
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

    private String formatApiDate(String value) {
        if (value == null || value.isBlank()) {
            return "";
        }
        DateTimeFormatter output = DateTimeFormatter.ofPattern("MMMM d, yyyy, h:mm a");
        try {
            return OffsetDateTime.parse(value).format(output);
        } catch (DateTimeParseException ignored) {
        }
        try {
            return LocalDateTime.parse(value).format(output);
        } catch (DateTimeParseException ignored) {
        }
        try {
            String cleaned = value.replace("T", " ");
            if (cleaned.contains(".")) {
                cleaned = cleaned.substring(0, cleaned.indexOf('.'));
            }
            if (cleaned.contains(" ")) {
                return LocalDateTime.parse(cleaned, DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")).format(output);
            }
            return LocalDate.parse(cleaned).format(DateTimeFormatter.ofPattern("MMMM d, yyyy"));
        } catch (DateTimeParseException ignored) {
        }
        return value;
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

    private boolean confirm(String title, String message) {
        Alert alert = new Alert(Alert.AlertType.CONFIRMATION);
        alert.setTitle(title);
        alert.setHeaderText(null);
        alert.setContentText(message);
        return alert.showAndWait().filter(button -> button == javafx.scene.control.ButtonType.OK).isPresent();
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
