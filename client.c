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

  n = sendto(fd, "SYN", 3, 0, (struct sockaddr *) server, server_len);
  if (n < 0)
  {
    perror("Error sending SYN packet\n");
    return -1;
  }

  printf("SYN sent\n");

  memset(msg, 0, 32);
  n = recvfrom(fd, &msg, 32, 0, (struct sockaddr *) server, &server_len);

  if (n < 0) {
    perror("Error receiving SYN-ACK");
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
  n = sendto(fd, "ACK", 3, 0, (struct sockaddr *) server, server_len);
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

  struct sockaddr_in adresse;
  int port = 1234;
  int valid = 1;
  // int recvsize = 0;
  // char msg[RCVSIZE];
  // char blanmsg[RCVSIZE];

  //create socket
  int server_desc = socket(AF_INET, SOCK_DGRAM, 0);

  // handle error
  if (server_desc < 0)
  {
    perror("cannot create socket\n");
    return -1;
  }

  setsockopt(server_desc, SOL_SOCKET, SO_REUSEADDR, &valid, sizeof(int));

  adresse.sin_family = AF_INET;
  adresse.sin_port = htons(port);
  adresse.sin_addr.s_addr = htonl(INADDR_LOOPBACK);

  // connect
  //int rc = connect(server_desc, (struct sockaddr *)&adresse, sizeof(adresse));
  //printf("value of connect is: %d\n", rc);

  // handle error
  /*
  if (rc < 0)
  {
    perror("connect failed\n");
    return -1;
  }
  */

  int data_port = tcp_over_udp_connect(server_desc, &adresse);

  if (data_port < 0) {
    printf("Error opening connection\n");
    return -1;
  }

  printf("Data port: %d\n", data_port);

  
  /*
  int cont= 1;
  while (cont) {
    memset(&msg, 0, RCVSIZE);
    memset(&blanmsg, 0, RCVSIZE);
    printf("Entrez votre message\n");
    fgets(msg,255,stdin);
    recvsize = write(server_desc, msg, strlen(msg));
    if (recvsize < 0)
    {
         perror("ERROR writing to socket");
    }
    fflush(stdin);
    recvsize = read(server_desc, &blanmsg, RCVSIZE);
    printf("server(%d)> %s\n", recvsize, blanmsg);
  }
  */

  close(server_desc);
  return 0;
}