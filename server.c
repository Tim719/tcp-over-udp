#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/select.h>
#include <sys/time.h>

#define RCVSIZE 1024

int main (int argc, char *argv[]) {

  struct sockaddr_in adresse, client;
  socklen_t client_size = sizeof(client);
  int port = 0;
  int msgSize = 0;
  char buffer[RCVSIZE];

  if (argc != 2) {
    printf("USAGE: server.c <port>\n");
    return 0;
  }

  port = atoi(argv[1]);

  if (port < 0) {
    printf("Port number must be greater than 0\n");
  }

  //create socket
  int server_udp = socket(AF_INET, SOCK_DGRAM, 0);
  int optval = 1;
	setsockopt(server_udp, SOL_SOCKET, SO_REUSEADDR, (const void *)&optval, sizeof(int));

  //handle error
  if (server_udp < 0) {
    perror("Cannot create socket\n");
    return -1;
  }


  adresse.sin_family= AF_INET;
  adresse.sin_port= htons(port);
  adresse.sin_addr.s_addr= htonl(INADDR_ANY);

  if (bind(server_udp, (struct sockaddr*) &adresse, sizeof(adresse)) == -1) {
    perror("UDP Bind failed\n");
    close(server_udp);
    return -1;
  }


  while (1) {
    printf("Accepting connections on port %d\n", port);
    
    // Serveur UDP
    memset(buffer,0,RCVSIZE);
    //int msgSize = read(server_udp, buffer,RCVSIZE);
    msgSize = recvfrom(server_udp, &buffer, RCVSIZE, 0, (struct sockaddr *) &client, &client_size);

    if (msgSize < 0) {
      break;
    }

    if (msgSize > 0) {
      printf("UDP> %s",buffer);
      msgSize = sendto(server_udp, &buffer, strlen(buffer), 0, (struct sockaddr *) &client, client_size);
      printf("%d bytes sent\n", msgSize);
    }
  }
  
  printf("Closing UDP server\n");
  close(server_udp);
  return 0;
}
