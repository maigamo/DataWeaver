#!/bin/bash

# 端口开放脚本
# 自动识别系统使用的防火墙类型（iptables或firewalld）
# 检查指定端口是否开放，如果未开放则进行配置
# 确保配置在系统重启后仍然生效
# 最后测试本机服务是否能够连接到公网

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认端口列表（可根据需要修改）
PORTS=("10010" "10086")

# 检查是否以root权限运行
check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo -e "${RED}错误: 此脚本需要root权限运行${NC}"
        echo "请使用 sudo 或 root 用户运行此脚本"
        exit 1
    fi
}

# 检测系统使用的防火墙类型
detect_firewall() {
    echo -e "${BLUE}正在检测系统防火墙类型...${NC}"
    
    # 检查firewalld是否安装并运行
    if command -v firewall-cmd &> /dev/null && systemctl is-active --quiet firewalld; then
        echo -e "${GREEN}检测到系统使用 firewalld${NC}"
        FIREWALL_TYPE="firewalld"
        return
    fi
    
    # 检查iptables是否安装
    if command -v iptables &> /dev/null; then
        echo -e "${GREEN}检测到系统使用 iptables${NC}"
        FIREWALL_TYPE="iptables"
        return
    fi
    
    echo -e "${YELLOW}警告: 未检测到支持的防火墙系统${NC}"
    echo "系统可能没有安装防火墙或使用其他防火墙系统"
    FIREWALL_TYPE="none"
}

# 检查端口是否已开放
check_port_open() {
    local port=$1
    echo -e "${BLUE}检查端口 $port 是否已开放...${NC}"
    
    case $FIREWALL_TYPE in
        "firewalld")
            if firewall-cmd --list-ports | grep -q "$port/tcp"; then
                echo -e "${GREEN}端口 $port 已开放${NC}"
                return 0
            else
                echo -e "${YELLOW}端口 $port 未开放${NC}"
                return 1
            fi
            ;;
        "iptables")
            if iptables -L INPUT -n | grep -q "dpt:$port"; then
                echo -e "${GREEN}端口 $port 已开放${NC}"
                return 0
            else
                echo -e "${YELLOW}端口 $port 未开放${NC}"
                return 1
            fi
            ;;
        "none")
            echo -e "${YELLOW}未检测到防火墙，假设端口已开放${NC}"
            return 0
            ;;
    esac
}

# 开放端口
open_port() {
    local port=$1
    echo -e "${BLUE}正在开放端口 $port...${NC}"
    
    case $FIREWALL_TYPE in
        "firewalld")
            # 添加端口到防火墙规则
            firewall-cmd --permanent --add-port=$port/tcp
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}成功添加端口 $port 到防火墙规则${NC}"
                # 重新加载防火墙配置
                firewall-cmd --reload
                echo -e "${GREEN}防火墙规则已重新加载${NC}"
                return 0
            else
                echo -e "${RED}添加端口 $port 到防火墙规则失败${NC}"
                return 1
            fi
            ;;
        "iptables")
            # 添加端口到iptables规则
            iptables -A INPUT -p tcp --dport $port -j ACCEPT
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}成功添加端口 $port 到iptables规则${NC}"
                # 保存iptables规则以确保重启后仍然生效
                if command -v iptables-save &> /dev/null; then
                    if [ -d "/etc/iptables" ]; then
                        iptables-save > /etc/iptables/rules.v4
                    else
                        mkdir -p /etc/iptables
                        iptables-save > /etc/iptables/rules.v4
                    fi
                    
                    # 确保启动时加载规则
                    if [ ! -f "/etc/network/if-pre-up.d/iptables" ]; then
                        echo '#!/bin/sh' > /etc/network/if-pre-up.d/iptables
                        echo 'iptables-restore < /etc/iptables/rules.v4' >> /etc/network/if-pre-up.d/iptables
                        chmod +x /etc/network/if-pre-up.d/iptables
                    fi
                    
                    echo -e "${GREEN}iptables规则已保存，将在系统重启后生效${NC}"
                else
                    # 如果没有iptables-save命令，尝试使用service保存
                    if command -v service &> /dev/null && service iptables save &> /dev/null; then
                        echo -e "${GREEN}iptables规则已保存，将在系统重启后生效${NC}"
                    else
                        echo -e "${YELLOW}警告: 无法保存iptables规则，系统重启后可能需要重新配置${NC}"
                        echo "请手动保存iptables规则或安装iptables-persistent包"
                    fi
                fi
                return 0
            else
                echo -e "${RED}添加端口 $port 到iptables规则失败${NC}"
                return 1
            fi
            ;;
        "none")
            echo -e "${YELLOW}未检测到防火墙，无需开放端口${NC}"
            return 0
            ;;
    esac
}

# 测试端口连通性
test_port_connectivity() {
    local port=$1
    echo -e "${BLUE}测试端口 $port 连通性...${NC}"
    
    # 检查本地服务是否在监听该端口
    if command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":$port "; then
            echo -e "${GREEN}本地服务正在监听端口 $port${NC}"
        else
            echo -e "${YELLOW}警告: 未检测到本地服务监听端口 $port${NC}"
            echo "请确保相关服务已启动"
            return 1
        fi
    elif command -v ss &> /dev/null; then
        if ss -tuln | grep -q ":$port "; then
            echo -e "${GREEN}本地服务正在监听端口 $port${NC}"
        else
            echo -e "${YELLOW}警告: 未检测到本地服务监听端口 $port${NC}"
            echo "请确保相关服务已启动"
            return 1
        fi
    else
        echo -e "${YELLOW}警告: 无法检测本地服务状态，请确保相关服务已启动${NC}"
    fi
    
    # 测试公网连通性
    echo -e "${BLUE}测试公网连通性...${NC}"
    if command -v curl &> /dev/null; then
        # 获取公网IP
        PUBLIC_IP=$(curl -s https://api.ipify.org)
        if [ -n "$PUBLIC_IP" ]; then
            echo -e "${GREEN}公网IP: $PUBLIC_IP${NC}"
            echo -e "${YELLOW}请尝试从外部网络访问 http://$PUBLIC_IP:$port 验证连通性${NC}"
        else
            echo -e "${RED}无法获取公网IP，请检查网络连接${NC}"
        fi
    else
        echo -e "${YELLOW}未安装curl工具，无法获取公网IP${NC}"
        echo "请安装curl或手动测试公网连通性"
    fi
}

# 主函数
main() {
    echo -e "${BLUE}===== 端口开放配置脚本 =====${NC}"
    
    # 检查root权限
    check_root
    
    # 检测防火墙类型
    detect_firewall
    
    # 处理每个端口
    for port in "${PORTS[@]}"; do
        # 检查端口是否已开放
        if ! check_port_open "$port"; then
            # 如果端口未开放，则开放端口
            open_port "$port"
        fi
        
        # 测试端口连通性
        test_port_connectivity "$port"
    done
    
    echo -e "${GREEN}===== 端口配置完成 =====${NC}"
    echo "如需添加更多端口，请编辑脚本中的PORTS数组"
}

# 执行主函数
main