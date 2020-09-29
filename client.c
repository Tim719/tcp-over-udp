#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define RCVSIZE 1024

int tcp_over_udp_connect(int fd, struct sockaddr_in *server)
{
  char msg[32];
  int n;
  socklen_t server_len = sizeof(struct sockaddr);
  printf("Sending SYN\n");

  n = sendto(fd, "SYN\n", 4, 0, (struct sockaddr *) server, server_len);
  if (n < 0)
  {
    perror("Error sending SYN packet\n");
    return -1;
  }

  printf("SYN sent\n");

  memset(msg, 0, 32);
  n = recvfrom(fd, &msg, 32, 0, (struct sockaddr *) server, &server_len);

  if (n < 0) {
    perror("Error receiving SYN-ACK\n");
    return -1;
  }

  if (strncmp(msg, "SYN-ACK", 7) != 0)
  {
    perror("SYN-ACK not received\n");
    return -1;
  }

  printf("SYN-ACK received\n");

  char *data_port = malloc(6);

  strncpy(data_port, msg + 8, 6);

  printf("Sending ACK\n");
  n = sendto(fd, "ACK\n", 4, 0, (struct sockaddr *) server, server_len);
  if (n < 0)
  {
    perror("Error sending ACK packet\n");
    return -1;
  }

  printf("ACK sent\n");
  return atoi(data_port);
}

int main(int argc, char *argv[])
{

  struct sockaddr_in address;
  int port = 1234;
  int valid = 1;
  int recvsize = 0;
  char msg[RCVSIZE];
  char blanmsg[RCVSIZE];
  char* server_ip;

  if (argc != 3)
  {
    printf("USAGE: client <server> <port>\n");
    return 0;
  }

  port = atoi(argv[2]);
  server_ip = argv[1];

  if (port < 0)
  {
    printf("Port number must be greater than 0\n");
  }

  //create socket
  int server_desc = socket(AF_INET, SOCK_DGRAM, 0);

  // handle error
  if (server_desc < 0)
  {
    perror("cannot create socket\n");
    return -1;
  }

  setsockopt(server_desc, SOL_SOCKET, SO_REUSEADDR, &valid, sizeof(int));

  address.sin_family = AF_INET;
  address.sin_port = htons(port);

  printf("IP: %s\n", server_ip);

  if (inet_aton(server_ip, &address.sin_addr) < 0) {
    perror("Error binding address\n");
    return -1;
  }

  int data_port = tcp_over_udp_connect(server_desc, &address);

  if (data_port < 0) {
    printf("Error opening connection\n");
    return -1;
  }

  printf("Data port: %d\n", data_port);

  if (data_port < 1) {
    perror("Error receiving data port\n");
    return -1;
  }

  address.sin_port = htons(data_port);

  socklen_t address_len = sizeof(struct sockaddr);

  while (1) {
    memset(&msg, 0, RCVSIZE);
    memset(&blanmsg, 0, RCVSIZE);
    printf("> ");
    fgets(msg,255,stdin);

    if (strcmp(msg, "stop\n") == 0) {
      recvsize = sendto(server_desc, "FIN\n", 4, 0, (struct sockaddr *) &address, address_len);
      break;
    }

    recvsize = sendto(server_desc, &msg, strlen(msg), 0, (struct sockaddr *) &address, address_len);
    if (recvsize < 0)
    {
         perror("ERROR writing to socket");
    }

    fflush(stdin);

    recvsize = recvfrom(server_desc, &blanmsg, RCVSIZE, 0, (struct sockaddr *) &address, &address_len);
    printf("server(%d)> %s\n", recvsize, blanmsg);
  }

  close(server_desc);
  return 0;
}