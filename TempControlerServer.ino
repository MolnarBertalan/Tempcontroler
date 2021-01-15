#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <PID_v1.h>

struct MSG {
  char Operator;
  char Value[22];  
};


WiFiServer server(80);                                              //(port)
WiFiClient client;                                                  //(cliensek max száma-1)
int status = WL_IDLE_STATUS;
bool IsConnected;

MSG message;

//PID
int Mode = 0;
double Setpoint = 0.0000, Input=0.0000, Output=0.0000, PWM=0.0000;  //Define Variables we'll be connecting to
double Kp=0.0000, Ki=0.0000, Kd=0.0000;                             //Define the Tuning Parameters
PID TPID(&Input, &Output, &Setpoint, Kp, Ki, Kd, DIRECT);

unsigned long t_measured = 0;
float measureinterval = 1;

//HandleServer----------------------------------------------------------------------------
void Con(const char *&ssid ,const char *&passkey){

  Serial.print("Connecting to ");
  Serial.println(ssid);
    
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, passkey);
    
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");}

  Serial.println("\nWiFi connected");  
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
};

void Broadcast(const char *&ssid ,const char *&passkey){

  Serial.println("Configuring access point...");
    
  WiFi.mode(WIFI_AP);
  WiFi.softAP(ssid);
  
  IPAddress myIP = WiFi.softAPIP();
  
  Serial.print("AP IP address: ");
  Serial.println(myIP);
};

void StartServer(int &mod) {

  if (mod == 0){
    const char *ssid    = "NodeMCU";
    const char *passkey = "12345678";
    Broadcast(ssid,passkey);}

  if (mod == 1){
    const char *ssid    = "********";
    const char *passkey = "********";
    Con(ssid,passkey);}

  Serial.println("Starting server...");
  server.begin();
  Serial.println("Server Started.");
};

//Messaging-------------------------------------------------------------------------------

void SendMessage(char Operator, char* Value){
  Serial.print(Operator);
  Serial.print(':');
  Serial.println(Value);
  client.println((String)Operator + ':' + Value);
  delay(100);}

void GetMessage(){
  String res = "";
  bool Exit = false;
  
  do {
    char s = client.read();
    if (s != '\n'){
      Serial.println(s);
      //append(res,s);}
      res += s;}
    else{
      Exit = true;}
  } while (!Exit);
  
  Serial.println("Over");
  Serial.println(res);
  message.Operator = res[0];
  for (int i=2; i<=res.length();i++){
  message.Value[i-2] = res[i];}
  Serial.println(message.Operator);
  Serial.println(message.Value);}

void HandleMessage(){
  char buf[9];
  
  switch (message.Operator) {
    case 'M':
      Mode = atoi(message.Value);
      switch (Mode){
        case 0:
          TPID.SetMode(MANUAL);
          Output = 0;
          break;
        case 1:
          TPID.SetMode(MANUAL);
          Output = 0;
          break;
        case 2:
          TPID.SetMode(AUTOMATIC);
          break;}
      break;
    case 'm':
      dtostrf(Mode,1,0,buf);
      SendMessage('M',buf);
      break;
    case 'P':
      Kp = atof(message.Value);
      Serial.print(Kp);
      TPID.SetTunings(Kp,Ki,Kd);      
      break;
    case 'p':
      dtostrf(TPID.GetKp(),4,3,buf);
      SendMessage('P',buf);
      break;
    case 'I':
      Ki = atof(message.Value);
      Serial.print(Ki);
      TPID.SetTunings(Kp,Ki,Kd);
      break;
    case 'i':
      dtostrf(TPID.GetKi(),4,3,buf);
      SendMessage('I',buf);
      break;
    case 'D':
      Kd = atof(message.Value);
      Serial.print(Kd);
      TPID.SetTunings(Kp,Ki,Kd);
      break;
    case 'd':
      dtostrf(TPID.GetKd(),4,3,buf);
      SendMessage('D',buf);
      break;
    case 'O':
      Output = atof(message.Value);
      break;
    case 'o':
      dtostrf(Output,4,3,buf);
      SendMessage('O',buf);
      break;
    case 'S':
      Setpoint = atof(message.Value);
      break;
    case 's':
      dtostrf(Setpoint,4,3,buf);
      SendMessage('S',buf);
      break;
    case 'n':
      t_measured = millis()/1000;
      dtostrf(t_measured,7,0,buf);
      SendMessage('N',buf);
      break;
    case 't':
      ReadInput();
      dtostrf(Input,4,3,buf);
      SendMessage('T',buf);
      break;
    default:
      SendMessage('R',"Operator not recognized");
      break;}
}

//HandleClient----------------------------------------------------------------------------

void HandleClient(){

  if (!client.connected()){
    client = server.available();
    
    if (IsConnected){
      Serial.println("Client Disconnected");
      client.stop();
      IsConnected = false;}}
            
  if(client.connected() && !IsConnected){
    client.flush();
    Serial.println("New client");
    SendMessage('R',"Hello Client!");  
    IsConnected = true;}
};

//ReadInput-------------------------------------------------------------------------------
void ReadInput(){
  Serial.println("reading");
  Input = analogRead(A0);
  Input = analogRead(A0);
  Serial.println(Input);
}

void WriteOutput(){
  switch (Mode){
    case 0:
      break;
    case 1:
      break;
    case 2:
      TPID.Compute();
      break;}
  if (Output !=0){
    PWM = map(Output, 0, 1023, 266, 1023);}
    
  analogWrite(D2, PWM);
}

void UpdateClient(){
  Serial.println("Starting update");
  char Tbuf[9];
  char Obuf[9];
  char Nbuf[10];

  dtostrf(Input,4,3,Tbuf);
  SendMessage('T',Tbuf);
  
  dtostrf(Output,4,3,Obuf);
  SendMessage('O',Obuf);
  
  dtostrf(t_measured,7,1,Nbuf);
  SendMessage('N',Nbuf);
}

//Main------------------------------------------------------------------------------------

void setup(){
  int Ans;
  Serial.begin(115200);
  delay(5000);
  Serial.println("Wifi mode? 0:AP 1:STA");
  
  do{
    delay(100);
    if (Serial.available() >0){   
      Ans = Serial.read()-48;
      Serial.println(Ans);}
    if (millis() > 20000){
      Ans = 0;}
  }while(Ans != 0 && Ans != 1);
  
  StartServer(Ans);
}

void loop() {
  if (millis()/1000-t_measured > measureinterval){
    t_measured = millis()/1000;
    ESP.wdtFeed();
    if (Mode != 0) {
      ReadInput();
      WriteOutput();
      if (client.connected()){
        UpdateClient();}}}
  
  HandleClient();
  delay(100);
  if (client.available()){
    GetMessage();
    Serial.print("Message is: ");
    Serial.print(message.Operator);
    Serial.print(':');
    Serial.println(message.Value);
    HandleMessage();}
}
