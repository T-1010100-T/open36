FROM eclipse-temurin:21-jdk-alpine
WORKDIR /app
COPY target/Open436-Enrollment-0.0.1-SNAPSHOT.jar app.jar
EXPOSE 8084
ENTRYPOINT ["java", "-jar", "app.jar"]
