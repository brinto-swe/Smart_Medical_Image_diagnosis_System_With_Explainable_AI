import javafx.geometry.Pos;
import javafx.scene.Node;
import javafx.scene.control.Label;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Region;
import javafx.scene.layout.StackPane;

public final class StatusViews {
    private StatusViews() {
    }

    public static Region dot(boolean online) {
        Region dot = new Region();
        dot.getStyleClass().addAll("status-dot", online ? "online" : "offline");
        dot.setMinSize(12, 12);
        dot.setPrefSize(12, 12);
        dot.setMaxSize(12, 12);
        return dot;
    }

    public static HBox pill(boolean online) {
        Label text = new Label(online ? "Online" : "Offline");
        text.getStyleClass().addAll("status-text", online ? "online" : "offline");
        HBox pill = new HBox(6, dot(online), text);
        pill.setAlignment(Pos.CENTER_LEFT);
        pill.getStyleClass().addAll("status-pill", online ? "online" : "offline");
        return pill;
    }

    public static StackPane avatarWithStatus(Node avatar, boolean online) {
        StackPane stack = new StackPane(avatar, dot(online));
        stack.getStyleClass().add("avatar-status-stack");
        StackPane.setAlignment(avatar, Pos.CENTER);
        StackPane.setAlignment(stack.getChildren().get(1), Pos.BOTTOM_RIGHT);
        return stack;
    }
}
