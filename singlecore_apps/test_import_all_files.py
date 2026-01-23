"""
CEISA Excel Import Test Script
Tests import of all 10 Excel files in dry_run mode
Reports success/failure and any mapping issues
"""

import frappe
import os
import json
from datetime import datetime

# Import the function we're testing
from singlecore_apps.api.ceisa_import import import_ceisa_excel

EXCEL_DIR = "/home/acer25/frappe-bench/base erp xls"

def run_import_test():
    """Test import for all Excel files"""
    
    # Get all xlsx files
    excel_files = [f for f in os.listdir(EXCEL_DIR) if f.endswith('.xlsx') and ':' not in f]
    excel_files.sort()
    
    print(f"\n{'='*80}")
    print(f"CEISA EXCEL IMPORT TEST - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing {len(excel_files)} files in DRY RUN mode (no data will be saved)")
    print(f"{'='*80}\n")
    
    results = []
    
    for idx, filename in enumerate(excel_files, 1):
        filepath = os.path.join(EXCEL_DIR, filename)
        print(f"\n[{idx}/{len(excel_files)}] Testing: {filename}")
        print("-" * 60)
        
        try:
            # Read file as base64 (simulating upload)
            import base64
            with open(filepath, 'rb') as f:
                file_content = base64.b64encode(f.read()).decode('utf-8')
            
            # Run import in dry_run mode
            result = import_ceisa_excel(file_content, dry_run=True)
            
            status = result.get('status', 'unknown')
            audit = result.get('audit', {})
            
            if status == 'success':
                print(f"  ✅ STATUS: SUCCESS")
                
                # Print statistics
                stats = audit.get('stats', {})
                if stats:
                    print(f"  📊 Records processed:")
                    for table, count in stats.items():
                        print(f"      - {table}: {count}")
                
                # Print warnings
                unmapped = audit.get('unmapped_columns', {})
                missing = audit.get('missing_columns', {})
                
                if unmapped:
                    print(f"  ⚠️  Unmapped columns (in Excel but not in code):")
                    for sheet, cols in unmapped.items():
                        print(f"      {sheet}: {', '.join(cols[:5])}{'...' if len(cols) > 5 else ''}")
                
                if missing:
                    print(f"  ⚠️  Missing columns (expected by code but not in Excel):")
                    for sheet, cols in missing.items():
                        print(f"      {sheet}: {', '.join(cols[:5])}{'...' if len(cols) > 5 else ''}")
                
                results.append({
                    'file': filename,
                    'status': 'SUCCESS',
                    'stats': stats,
                    'unmapped_count': sum(len(v) for v in unmapped.values()),
                    'missing_count': sum(len(v) for v in missing.values())
                })
                
            else:
                print(f"  ❌ STATUS: FAILED")
                print(f"  📝 Message: {result.get('message', 'No message')[:200]}")
                results.append({
                    'file': filename,
                    'status': 'FAILED',
                    'message': result.get('message', '')[:500]
                })
                
        except Exception as e:
            print(f"  ❌ EXCEPTION: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                'file': filename,
                'status': 'EXCEPTION',
                'error': str(e)
            })
        
        # Rollback any changes
        frappe.db.rollback()
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    success_count = len([r for r in results if r['status'] == 'SUCCESS'])
    failed_count = len([r for r in results if r['status'] == 'FAILED'])
    exception_count = len([r for r in results if r['status'] == 'EXCEPTION'])
    
    print(f"  ✅ Success: {success_count}/{len(results)}")
    print(f"  ❌ Failed: {failed_count}/{len(results)}")
    print(f"  💥 Exceptions: {exception_count}/{len(results)}")
    
    # Save detailed report
    report_path = "/home/acer25/frappe-bench/import_test_report.json"
    with open(report_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_files': len(results),
            'success': success_count,
            'failed': failed_count,
            'exceptions': exception_count,
            'results': results
        }, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    return results

if __name__ == "__main__":
    # Initialize Frappe
    frappe.init(site='dens9.com')
    frappe.connect()
    
    try:
        run_import_test()
    finally:
        frappe.destroy()
