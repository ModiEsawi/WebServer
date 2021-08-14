import socket
import os
import sys

# creating a TCP server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', int(sys.argv[1])))
server.listen(5)

'''read the data from the client 1 byte by a time to take care of cases when more then one request is in the buffer at the 
same time'''


def readAll(sock):
    maxSize = 1
    readData = b''
    while True:
        read = sock.recv(maxSize)
        readData += read
        if readData[-4:] == b'\r\n\r\n' or read == b'' or readData == b'\n' or readData == b'\r\n':  # we finished reading the request or the buffer is now empty
            break
    return readData


'''after reading the clients request we will call the "returnAnswer" method to return the right answer'''


def acceptClient(clientSocket):
    try:
        data = readAll(clientsSocket)
        print(data.decode())
        if data == b'' or data == b'\n' or data == b'\r\n':
            clientsSocket.close()
            return
        returnAnswer(data, clientSocket)
    except socket.timeout:  # client didnt respond for one second
        clientsSocket.close()
        return


''' checks if the connection Status is "close" we will close the socket and move on to the next client'''


def checkForClosing(status, givenSocket):
    if status == "close":
        givenSocket.close()
        return False
    return True


'''returning the right answer based on the clients request'''


def returnAnswer(data, client_socket):
    address = data.decode()
    lines = address.split("\r\n")
    get = lines[0]
    if "GET " not in get:
        client_socket.close()
        return
    requestedFile = get.split(" ")[1]
    connectionStatus = ""
    for line in lines:
        if "Connection: " in line:
            connectionStatus = line.split(" ")[1]
    if connectionStatus == "":
        client_socket.close()
        return
    script_dir = os.path.abspath(os.path.dirname(__file__))  # <-- absolute dir the script is in
    file_path = os.path.join(script_dir, "files" + str(requestedFile))
    if requestedFile == "/" or requestedFile == "/redirect":
        rel_path = ""
        firstPart = ""
        if requestedFile == "/":
            rel_path = "files\index.html"
            firstPart = "HTTP/1.1 200 OK\r\nConnection: " + str(connectionStatus)
            ending = "\r\nContent-Length: "
            firstPart += ending
        elif requestedFile == "/redirect":
            ans = "HTTP/1.1 301 Moved Permanently\r\nConnection: close\r\nLocation: /result.html\r\n\r\n"
            client_socket.send(ans.encode())
            client_socket.close()
            return
        abs_file_path = os.path.join(script_dir, rel_path)
        HtmlFile = open(abs_file_path, 'r', encoding='utf-8')
        source_code = str(HtmlFile.read())
        HtmlFile.close()
        length = len(source_code)
        secondPart = str(length) + "\r\n\r\n" + source_code + "\r\n"
        answer = firstPart + secondPart
        client_socket.send(answer.encode())
        if not checkForClosing(connectionStatus, client_socket):
            return
        acceptClient(client_socket)  # calling the accept client again to check for more data to read in the buffer
    # if the path doesn't exist or the request is a directory we return 404
    elif not os.path.exists(file_path) or os.path.isdir(file_path):
        notFound = "HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n"
        client_socket.send(notFound.encode())
        client_socket.close()
        return
    # request for .jpg or .ico images sent in binary form as requested
    elif ".jpg" in requestedFile or ".ico" in requestedFile:
        path = "files" + str(requestedFile)
        abs_image_path = os.path.join(script_dir, path)
        imageFile = open(abs_image_path, "rb")
        binaryData = imageFile.read()
        connectionString = "Connection: " + connectionStatus
        HTTP_RESPONSE = b'\r\n'.join([
            b"HTTP/1.1 200 OK",
            bytes(connectionString, 'utf-8'),
            bytes("Content-Length: %s" % len(binaryData), 'utf-8'),
            b'', binaryData, b''
        ])
        client_socket.sendall(HTTP_RESPONSE)
        imageFile.close()
        if not checkForClosing(connectionStatus, client_socket):
            return
        acceptClient(client_socket)
    else:  # any other request (.css , .js files , and more)
        path = "files" + str(requestedFile)
        firstPart = "HTTP/1.1 200 OK\r\n" + "Connection: " + connectionStatus + "\r\n"
        abs_file_path = os.path.join(script_dir, path)
        file = open(abs_file_path, 'r', encoding='utf-8')
        source_code = str(file.read())
        length = len(source_code)
        file.close()
        secondPart = "Content-Length: " + str(length) + "\r\n\r\n" + source_code + "\r\n"
        answer = firstPart + secondPart
        client_socket.sendall(bytes(answer, 'utf-8'))
        if not checkForClosing(connectionStatus, client_socket):
            return
        acceptClient(client_socket)


# accept clients
while True:
    clientsSocket, client_address = server.accept()
    clientsSocket.settimeout(1)  # set the clients socket's timeout
    acceptClient(clientsSocket)
