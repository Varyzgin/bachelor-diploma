package server;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import org.java_websocket.server.WebSocketServer;
import org.java_websocket.WebSocket;
import org.java_websocket.handshake.ClientHandshake;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.InetSocketAddress;
import java.nio.file.Files;
import java.util.Map;

public class MainServer extends WebSocketServer {
    public MainServer(InetSocketAddress address) {
        super(address);
    }
    @Override
    public void onOpen(WebSocket conn, ClientHandshake handshake) {
        System.out.println("New connection from " + conn.getRemoteSocketAddress());
    }
    @Override
    public void onClose(WebSocket conn, int code, String reason, boolean remote) {
        System.out.println("Closed connection to " + conn.getRemoteSocketAddress() + " with exit code " + code + " additional info: " + reason);
    }
    @Override
    public void onMessage(WebSocket conn, String message) {
        System.out.println("Received message from " + conn.getRemoteSocketAddress() + ": " + message);
        JsonObject jsonObject = new Gson().fromJson(message, JsonObject.class);

        // Checking if the message is a request to send the file
        if (jsonObject.has("address")) {
            // Assuming the message is JSON with the data
            Gson gson = new Gson();
            Map<String, String> data = gson.fromJson(message, Map.class);

            // Creating and executing the Python script
            try {
                String args = "'" + gson.toJson(data) + "'";
                ProcessBuilder pb = new ProcessBuilder("python3", "/Users/dima/Desktop/Диплом/Code/4_use_model/map_generator.py", args);
                pb.redirectErrorStream(true);
                Process process = pb.start();

                BufferedReader in = new BufferedReader(new InputStreamReader(process.getInputStream()));
                StringBuilder result = new StringBuilder();
                String line;
                while ((line = in.readLine()) != null) {
                    result.append(line).append("\n");
                }
                process.waitFor();
                in.close();

                String city = data.get("city").replace(" ", "+");
                String address = data.get("address").replace(" ", "+");
                String area = data.get("area").replace(" ", "+");
                String year = data.get("year").replace(" ", "+");
                String floors = data.get("floors").replace(" ", "+");

                // Constructing the filename based on received data
                String fileName = String.format("/Users/dima/Desktop/Диплом/Data/prediction-for-%s-%s-%s-%s-%s.html",
                        city, address, area, year, floors);

                File file = new File(fileName);
                boolean fileExists = false;

                for (int i = 0; i < 15; i++) {
                    if (file.exists()) {
                        fileExists = true;
                        break;
                    }
                    System.out.println(i);
                    Thread.sleep(1000);
                }

                if (fileExists) {
                    String fileContent = new String(Files.readAllBytes(file.toPath()));
                    conn.send(fileContent);
                    System.out.println("Prediction file sent to client: " + conn.getRemoteSocketAddress());
                } else {
                    conn.send("Prediction file not found");
                    System.out.println("Prediction file not found for client: " + conn.getRemoteSocketAddress());
                }
            } catch (Exception e) {
                e.printStackTrace();
                conn.send("Error executing Python script");
            }
        }
        onClose(conn, 200, "Action completed", true);
    }
    @Override
    public void onError(WebSocket conn, Exception ex) {
        System.out.println("An error occurred on connection " + conn.getRemoteSocketAddress() + ":" + ex);
    }
    @Override
    public void onStart() {
        System.out.println("Server started successfully");
    }

    public static void main(String[] args) {
        String host = "localhost";
        int port = 3125;
        InetSocketAddress address = new InetSocketAddress(host, port);
        MainServer server = new MainServer(address);
        server.start();
        System.out.println("WebSocket server started on port: " + port);
    }
}