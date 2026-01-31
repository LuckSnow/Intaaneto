# Mạng Máy Tính (Computer Networks)

## Tổng Quan

**Mạng máy tính** là một tập hợp các thiết bị máy tính được kết nối với nhau để chia sẻ tài nguyên và thông tin. Các thiết bị này có thể là máy tính, máy chủ, thiết bị di động, hoặc các thiết bị IoT.

## Mô Hình OSI (Open Systems Interconnection)

### 7 Tầng của Mô Hình OSI:

#### 1. Physical Layer (Tầng Vật Lý)
- Truyền tải bits qua phương tiện vật lý
- Cáp đồng trục, cáp quang, sóng radio
- Hub, Repeater

#### 2. Data Link Layer (Tầng Liên Kết Dữ Liệu)
- MAC addressing
- Error detection và correction
- Frame transmission
- Switch, Bridge
- Protocols: Ethernet, Wi-Fi (IEEE 802.11)

#### 3. Network Layer (Tầng Mạng)
- IP addressing và routing
- Packet forwarding
- Router
- Protocols: IP, ICMP, IGMP

#### 4. Transport Layer (Tầng Vận Chuyển)
- End-to-end communication
- Segmentation và reassembly
- Flow control và error correction
- Protocols: TCP, UDP

#### 5. Session Layer (Tầng Phiên)
- Thiết lập, quản lý và kết thúc sessions
- Dialog control
- Synchronization

#### 6. Presentation Layer (Tầng Trình Diễn)
- Data translation và encryption
- Compression
- Format conversion
- SSL/TLS

#### 7. Application Layer (Tầng Ứng Dụng)
- User interface
- Network services cho applications
- Protocols: HTTP, FTP, SMTP, DNS, DHCP

## Mô Hình TCP/IP

### 4 Tầng của TCP/IP:

1. **Network Access Layer**: Tương đương Physical + Data Link trong OSI
2. **Internet Layer**: Tương đương Network Layer (IP, ICMP)
3. **Transport Layer**: TCP, UDP
4. **Application Layer**: HTTP, FTP, SMTP, DNS

## Địa Chỉ IP (IP Addressing)

### IPv4 (Internet Protocol version 4)
- 32-bit address
- Format: xxx.xxx.xxx.xxx (0-255)
- Ví dụ: 192.168.1.1
- Khoảng 4.3 tỷ địa chỉ

**Classes:**
- Class A: 1.0.0.0 to 126.255.255.255
- Class B: 128.0.0.0 to 191.255.255.255
- Class C: 192.0.0.0 to 223.255.255.255
- Class D: Multicast (224.0.0.0 to 239.255.255.255)
- Class E: Reserved (240.0.0.0 to 255.255.255.255)

**Private IP Ranges:**
- 10.0.0.0 to 10.255.255.255
- 172.16.0.0 to 172.31.255.255
- 192.168.0.0 to 192.168.255.255

### IPv6 (Internet Protocol version 6)
- 128-bit address
- Format: xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx (hexadecimal)
- Ví dụ: 2001:0db8:85a3:0000:0000:8a2e:0370:7334
- Khoảng 340 undecillion địa chỉ

### Subnet Mask
- Xác định phần network và host của IP address
- Ví dụ: 255.255.255.0 (/24)
- CIDR notation: 192.168.1.0/24

## Giao Thức Mạng Quan Trọng

### 1. TCP (Transmission Control Protocol)
- Connection-oriented
- Reliable, ordered delivery
- Flow control
- Error checking
- Sử dụng: HTTP, HTTPS, FTP, SMTP

### 2. UDP (User Datagram Protocol)
- Connectionless
- Fast, không đảm bảo delivery
- No error checking
- Sử dụng: DNS, DHCP, Video streaming, Gaming

### 3. HTTP/HTTPS
- **HTTP**: Port 80, unencrypted
- **HTTPS**: Port 443, encrypted với SSL/TLS
- Methods: GET, POST, PUT, DELETE, PATCH

### 4. DNS (Domain Name System)
- Chuyển đổi domain names thành IP addresses
- Hierarchical structure
- Port 53

### 5. DHCP (Dynamic Host Configuration Protocol)
- Tự động cấp phát IP addresses
- Quản lý IP pool
- Lease time

### 6. FTP (File Transfer Protocol)
- Port 21 (control), Port 20 (data)
- Transfer files giữa client và server
- SFTP, FTPS cho secure transfer

### 7. SMTP/POP3/IMAP
- **SMTP**: Gửi email (Port 25, 587)
- **POP3**: Nhận email (Port 110)
- **IMAP**: Nhận email với sync (Port 143)

### 8. SSH (Secure Shell)
- Port 22
- Remote access và command execution
- Encrypted connection

## Thiết Bị Mạng

### 1. Router
- Kết nối nhiều networks
- Routing packets giữa các networks
- NAT (Network Address Translation)
- Firewall

### 2. Switch
- Kết nối devices trong cùng network
- MAC address table
- Layer 2 hoặc Layer 3 switching

### 3. Hub
- Basic connectivity device
- Broadcast tất cả packets
- Không intelligent

### 4. Modem
- Modulate/Demodulate signals
- Kết nối local network với ISP

### 5. Access Point (AP)
- Wireless connectivity
- Bridge giữa wired và wireless networks

### 6. Firewall
- Security device/software
- Filter traffic dựa trên rules
- Prevent unauthorized access

## Các Loại Mạng

### 1. LAN (Local Area Network)
- Phạm vi nhỏ: office, home, building
- High speed
- Ethernet, Wi-Fi

### 2. WAN (Wide Area Network)
- Phạm vi rộng: cities, countries, continents
- Internet là WAN lớn nhất
- Leased lines, MPLS, VPN

### 3. MAN (Metropolitan Area Network)
- Phạm vi: city hoặc campus
- Fiber optic connections

### 4. PAN (Personal Area Network)
- Phạm vi rất nhỏ: personal space
- Bluetooth, USB, IrDA

### 5. WLAN (Wireless LAN)
- LAN sử dụng wireless technology
- Wi-Fi (IEEE 802.11)

### 6. VPN (Virtual Private Network)
- Encrypted tunnel qua public network
- Remote access
- Site-to-site connectivity

## Network Topologies

### 1. Bus Topology
- Một cable chính kết nối tất cả devices
- Simple, low cost
- Single point of failure

### 2. Star Topology
- Tất cả devices kết nối với central hub/switch
- Easy to manage
- Hub failure ảnh hưởng toàn bộ network

### 3. Ring Topology
- Devices kết nối thành vòng tròn
- Data travels in one direction
- Token passing

### 4. Mesh Topology
- Mọi device kết nối với mọi device khác
- Highly redundant
- Expensive

### 5. Hybrid Topology
- Kết hợp nhiều topologies
- Flexible

## Network Security

### Threats (Mối Đe Dọa):
1. **Malware**: Viruses, Worms, Trojans, Ransomware
2. **DoS/DDoS**: Denial of Service attacks
3. **Man-in-the-Middle**: Interception of communications
4. **Phishing**: Social engineering attacks
5. **SQL Injection**: Database attacks
6. **Zero-day Exploits**: Unknown vulnerabilities

### Security Measures:
1. **Firewall**: Hardware và software firewalls
2. **Encryption**: SSL/TLS, VPN, IPSec
3. **Authentication**: Passwords, 2FA, biometrics
4. **Access Control**: RBAC, ACLs
5. **IDS/IPS**: Intrusion Detection/Prevention Systems
6. **Antivirus/Antimalware**: Endpoint protection
7. **Network Segmentation**: VLANs, subnets
8. **Regular Updates**: Patches và updates

## Wireless Networks

### Wi-Fi Standards (IEEE 802.11):
- **802.11b**: 11 Mbps, 2.4 GHz
- **802.11g**: 54 Mbps, 2.4 GHz
- **802.11n**: 600 Mbps, 2.4/5 GHz
- **802.11ac**: 1300+ Mbps, 5 GHz (Wi-Fi 5)
- **802.11ax**: 9.6 Gbps, 2.4/5/6 GHz (Wi-Fi 6)
- **802.11be**: 46 Gbps, 2.4/5/6 GHz (Wi-Fi 7)

### Security:
- **WEP**: Deprecated, insecure
- **WPA**: Improved security
- **WPA2**: Strong encryption (AES)
- **WPA3**: Latest standard, enhanced security

## Cloud Networking

### Concepts:
- **SDN (Software-Defined Networking)**: Centralized network control
- **NFV (Network Functions Virtualization)**: Virtualized network services
- **Cloud Load Balancers**: Distribute traffic
- **CDN (Content Delivery Network)**: Distributed content delivery
- **Multi-Cloud Networking**: Connect multiple cloud providers

## Network Performance

### Metrics:
- **Bandwidth**: Maximum data transfer rate
- **Throughput**: Actual data transfer rate
- **Latency**: Time delay in transmission
- **Jitter**: Variation in latency
- **Packet Loss**: Percentage of lost packets

### QoS (Quality of Service):
- Traffic prioritization
- Bandwidth allocation
- Minimize latency cho critical applications

## Network Troubleshooting Tools

### Command-Line Tools:
- **ping**: Test connectivity
- **traceroute/tracert**: Trace packet path
- **ipconfig/ifconfig**: Network configuration
- **netstat**: Network statistics
- **nslookup/dig**: DNS lookup
- **arp**: ARP table

### Network Analyzers:
- Wireshark: Packet capture và analysis
- tcpdump: Command-line packet analyzer
- Nmap: Network scanner

## Xu Hướng Hiện Đại

1. **5G Networks**: Ultra-fast mobile connectivity
2. **IoT (Internet of Things)**: Billions of connected devices
3. **Edge Computing**: Processing at network edge
4. **SD-WAN**: Software-Defined WAN
5. **Zero Trust Security**: Never trust, always verify
6. **AI/ML in Networking**: Intelligent network management
7. **IPv6 Adoption**: Transition from IPv4

## Tham Khảo

Nội dung được tổng hợp từ:
- Wikipedia: Computer Network, Internet Protocol Suite
- RFC Documents (Internet Engineering Task Force)
- IEEE Standards
- Cisco Networking Academy

---

*Tài liệu này được tạo cho mục đích giáo dục trong hệ thống Intaaneto.*
