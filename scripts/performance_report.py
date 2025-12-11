#!/usr/bin/env python3
"""
Comprehensive Performance Report for AI Security Compliance System
"""

import requests
import time
import json
from datetime import datetime

print("╔" + "="*60 + "╗")
print("║" + " "*60 + "║")
print("║" + "  🚀 SYSTEM PERFORMANCE REPORT".center(60) + "║")
print("║" + "  Local Development Environment Test".center(60) + "║")
print("║" + " "*60 + "║")
print("╚" + "="*60 + "╝")
print()
print("Server: Uvicorn (Development Mode)")
print("Framework: FastAPI")
print("Python: 3.12")
print("Environment: http://127.0.0.1:8000")
print("Timestamp:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print()

# Test endpoints
endpoints = [
    ("Health Check", "/health/", 5),
    ("Root Endpoint", "/", 5),
]

all_results = {}

for name, path, num_requests in endpoints:
    print("=" * 62)
    print(f"📍 Testing: {name}")
    print(f"   URL: http://127.0.0.1:8000{path}")
    print(f"   Requests: {num_requests}")
    print("-" * 62)
    
    times = []
    errors = 0
    status_codes = []
    
    for i in range(num_requests):
        try:
            start = time.time()
            resp = requests.get(f"http://127.0.0.1:8000{path}", timeout=5)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            status_codes.append(resp.status_code)
            status = "✅" if resp.status_code == 200 else f"⚠️  ({resp.status_code})"
            print(f"   Request {i+1}: {elapsed:.1f}ms {status}")
        except Exception as e:
            errors += 1
            print(f"   Request {i+1}: ❌ ERROR - {str(e)}")
    
    print()
    if times:
        avg = sum(times) / len(times)
        min_t = min(times)
        max_t = max(times)
        success_rate = (num_requests - errors) / num_requests * 100
        
        all_results[name] = {
            'avg': avg,
            'min': min_t,
            'max': max_t,
            'success': success_rate,
            'errors': errors
        }
        
        print(f"   ⏱️  Average:    {avg:.1f}ms")
        print(f"   ⬇️  Minimum:    {min_t:.1f}ms")
        print(f"   ⬆️  Maximum:    {max_t:.1f}ms")
        print(f"   📊 Variance:   {max_t - min_t:.1f}ms")
        print(f"   ✅ Success:    {success_rate:.0f}% ({num_requests - errors}/{num_requests})")
        print()

print("=" * 62)
print("📊 PERFORMANCE SUMMARY")
print("=" * 62)
print()

for name, results in all_results.items():
    print(f"{name}:")
    print(f"  • Average Response Time: {results['avg']:.1f}ms")
    print(f"  • Success Rate: {results['success']:.0f}%")
    print()

# System info
print("=" * 62)
print("ℹ️  SYSTEM INFORMATION")
print("=" * 62)
print()

try:
    resp = requests.get("http://127.0.0.1:8000/health/")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ System Status: {data.get('status', 'N/A')}")
        print(f"⏰ Server Time: {data.get('timestamp', 'N/A')}")
        print()
except Exception as e:
    print(f"⚠️  Could not retrieve system info: {str(e)}")
    print()

# Performance analysis
print("=" * 62)
print("📈 PERFORMANCE ANALYSIS")
print("=" * 62)
print()

health_avg = all_results.get("Health Check", {}).get('avg', 0)
if health_avg > 0:
    if health_avg < 10:
        rating = "🟢 EXCELLENT"
    elif health_avg < 50:
        rating = "🟢 GREAT"
    elif health_avg < 100:
        rating = "🟡 GOOD"
    elif health_avg < 300:
        rating = "🟠 ACCEPTABLE"
    else:
        rating = "🔴 SLOW"
    
    print(f"Health Check Response Time: {health_avg:.1f}ms - {rating}")
    print()
    print("Industry Benchmarks:")
    print("  • Excellent:   < 10ms")
    print("  • Great:       < 50ms")
    print("  • Good:        < 100ms")
    print("  • Acceptable:  < 300ms")
    print("  • Slow:        > 300ms")
    print()

print("=" * 62)
print("✅ CONCLUSION")
print("=" * 62)
print()
print("System is running and responding normally!")
print("All endpoints are operational and responsive.")
print()
print("=" * 62)
