$env:PATH = 'C:\Users\mozad\Downloads\openjfx-26_windows-x64_bin-sdk\javafx\bin;' + $env:PATH
& 'C:\Program Files\Java\jdk-26\bin\javac.exe' --module-path '.\lib' --add-modules javafx.controls,javafx.fxml -d '.\bin' '.\src\*.java'
if ($LASTEXITCODE -eq 0) {
    & 'C:\Program Files\Java\jdk-26\bin\java.exe' --module-path '.\lib' --add-modules javafx.controls,javafx.fxml --enable-native-access=javafx.graphics -cp '.\bin' App
}
