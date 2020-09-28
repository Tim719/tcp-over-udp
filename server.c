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

int tcp_over_udp_accept(int fd, int data_port, struct sockaddr_in *client)
{
  printf("Waiting for connection\n");
  char buffer[32];
  int n;
  socklen_t client_size = sizeof(struct sockaddr);

  char* SYN_ACK = malloc(14);
  sprintf(SYN_ACK, "SYN-ACK-%d", data_port);

  memset(buffer, 0, 32);
  n = recvfrom(fd, &buffer, 32, 0, (struct sockaddr *) client, &client_size);

  printf("Message received : %s\n", buffer);

  if (strcmp(buffer, "SYN") != 0)
  {
    perror("Connection must start with SYN\n");
    return -1;
  }
  printf("SYN received\n");

  n = sendto(fd, SYN_ACK, strlen(SYN_ACK), 0, (struct sockaddr *) client, client_size);
  if (n < 0)
  {
    perror("Unable to send SYN-ACK\n");
    return -1;
  }
  printf("SYN-ACK sent\n");

  memset(buffer, 0, 32);

  n = recvfrom(fd, &buffer, 32, 0, (struct sockaddr *) client, &client_size);
  if (strcmp(buffer, "ACK") != 0)
  {
    perror("ACK not received\n");
    return -1;
  }
  printf("ACK received. Connected\n");

  return 0;
}

int main(int argc, char *argv[])
{
  printf("Henlo\n");
  struct sockaddr_in adresse, client;
  int port = 0;
  int data_port = 0;

  if (argc != 3)
  {
    printf("USAGE: server.c <control_port> <data_port>\n");
    return 0;
  }

  port = atoi(argv[1]);
  data_port = atoi(argv[2]);

  if (port < 0 || data_port < 0)
  {
    printf("Port number must be greater than 0\n");
  }

  //create socket
  int server_udp = socket(AF_INET, SOCK_DGRAM, 0);
  int optval = 1;
  setsockopt(server_udp, SOL_SOCKET, SO_REUSEADDR, (const void *)&optval, sizeof(int));

  //handle error
  if (server_udp < 0)
  {
    perror("Cannot create socket\n");
    return -1;
  }

  printf("Binding address...\n");

  adresse.sin_family = AF_INET;
  adresse.sin_port = htons(port);
  adresse.sin_addr.s_addr = htonl(INADDR_ANY);

  if (bind(server_udp, (struct sockaddr *)&adresse, sizeof(adresse)) == -1)
  {
    perror("UDP Bind failed\n");
    close(server_udp);
    return -1;
  }

  printf("Connecting...\n");

  // Serveur UDP
  int status = tcp_over_udp_accept(server_udp, data_port, &client);

  if (status == 0) {
    printf("Everything is fine my friend\n");
  }

  /*
  while (1) {
    printf("Accepting connections on port %d\n", port);
    
    // Serveur UDP
    memset(buffer,0,RCVSIZE);

    msgSize = recvfrom(server_udp, &buffer, RCVSIZE, 0, (struct sockaddr *) &client, &client_size);

    if (strcmp(buffer, "SYN")) {
      printf("SYN received\n");
      msgSize = sendto(server_udp, &SYN_ACK, strlen(SYN_ACK), 0, (struct sockaddr *) &client, client_size); 
      printf("SYN-ACK sent: %s\n", SYN_ACK);
      memset(buffer,0,RCVSIZE);
      msgSize = recvfrom(server_udp, &buffer, RCVSIZE, 0, (struct sockaddr *) &client, &client_size);
      if (strcmp(buffer, "ACK")) {
        printf("ACK received. Connected");
      }
    }

    if (msgSize < 0) {
      break;
    }

    if (msgSize > 0) {
      printf("UDP> %s",buffer);
      msgSize = sendto(server_udp, &buffer, strlen(buffer), 0, (struct sockaddr *) &client, client_size);
      printf("%d bytes sent\n", msgSize);
    }
  }
  */

  printf("Closing UDP server\n");
  close(server_udp);
  return 0;
}
