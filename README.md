# Tempcontroler
A prototípus egy szabályozási/ vezérlési folyamat automatizálását végzi.
A folyamat során a mért jellemző a hőmérséklet a szabályzott jellemző pedig egy kémiai reagens áramlási sebessége. 

A hőmérséklet mérését egy ellenálláshőmérővel oldottam meg, míg a reagenst egy perisztaltikus pumpa adagolja. A pumpa gyakorlatilag egy DC motor ami speciális fejjel van ellátva.
Célom volt, hogy a vezérlőd PC-ről Wifi hálózaton keresztül tudjuk beállítani és monitorozni, ezért a szoftver két részre oszlik: Egy PC-n futtatható Kliensre és egy a mikrokontorlleren futó szerverre. A két rész között TCP/IP kommunikációt valósítottam meg.

A felhasznált mikrokontroller egy NodeMCU v3 ami beépített WiFi modullal rendelkezik. 
