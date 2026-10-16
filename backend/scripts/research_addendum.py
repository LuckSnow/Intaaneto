"""Supplement six-PDF reports with corpus inventory and new-document comparisons."""
import argparse
import json
from pathlib import Path

from pdf_research_reporting import build_tables, read_scores, write_csv


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results',type=Path,required=True)
    parser.add_argument('--catalog',type=Path,required=True)
    parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--ratings',type=Path)
    parser.add_argument('--ingestion-timings',type=Path)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--new-source-ids',nargs='+',default=['PDF05','PDF06'])
    args=parser.parse_args()
    report=json.loads(args.results.read_text())
    catalog=json.loads(args.catalog.read_text())
    dataset=json.loads(args.dataset.read_text())
    scores=read_scores(args.ratings,report['cases'])
    overall,tables=build_tables(report,scores)
    out=args.output_dir;out.mkdir(parents=True,exist_ok=True,mode=0o700)
    inventory=[]
    for source in dataset['sources']:
        meta=next(row for row in catalog if row['pdf_id']==source['id'])
        file=args.dataset.parent/source['pdf_file']
        inventory.append(dict(meta,pdf_bytes=file.stat().st_size,pdf_sha256=source['pdf_sha256'],
                              questions=sum(c['source_id']==source['id'] for c in dataset['cases'])))
    write_csv(out/'tables/corpus_inventory.csv',list(inventory[0]),inventory)
    fresh=[r for r in tables['by_pdf'] if r['source_id'] in args.new_source_ids]
    write_csv(out/'tables/new_pdfs_comparison.csv',list(fresh[0]),fresh)
    new_rows=[r for r in report['cases'] if r['source_id'] in args.new_source_ids]
    write_csv(out/'new_pdfs_answers.csv',['id','question','reference_answer','answer','error','latency_ms','grounded','score'],
              [dict(r,score=scores.get(r['id'])) for r in new_rows])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.family':'DejaVu Sans','pdf.fonttype':42,'svg.fonttype':'path','font.size':10})
    def save(fig,name):
        for ext in ['png','svg','pdf']:fig.savefig(out/f'{name}.{ext}',dpi=300,facecolor='white')
        plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained')
    for ax,key,label in zip(axes,['pages','extracted_chars','chunk_count'],['Số trang PDF','Ký tự trích xuất','Số chunk đang active']):
        values=[r[key] for r in inventory]
        ax.bar([r['pdf_id'] for r in inventory],values,color='#0072B2')
        ax.set(ylabel=label,title=label,ylim=(0,None))
        for i,v in enumerate(values):ax.text(i,v,str(v),ha='center',va='bottom',fontsize=8)
    save(fig,'corpus_profile')
    fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained')
    for ax,key,label,factor in zip(axes,['mean_s','expected_page_overlap_proxy','strict_accuracy'],['Latency TB thành công (giây)','Chồng lấp trang nguồn (%)','Accuracy sơ bộ Codex (%)'],[1,100,100]):
        values=[r[key]*factor if r[key] is not None else np.nan for r in fresh]
        ax.bar([r['source_id'] for r in fresh],values,color='#0072B2');ax.set(title=label,ylim=(0,100 if factor==100 else None))
        for i,v in enumerate(values):
            ax.text(i,0 if np.isnan(v) else v,'Chờ chấm' if np.isnan(v) else f'{v:.2f}',ha='center',va='bottom')
    fig.suptitle('Hai PDF mới: PDF05 = Node.js; PDF06 = Router Express — điểm nội dung cần giảng viên duyệt',fontsize=10)
    save(fig,'new_pdfs_metrics')
    ingestion=[]
    if args.ingestion_timings:
        ingestion=json.loads(args.ingestion_timings.read_text())
        for row in ingestion:
            row['pdf_id']=next(r['pdf_id'] for r in inventory if r['lesson_id']==row['lesson_id'])
        ingestion.sort(key=lambda row:row['pdf_id'])
        write_csv(out/'tables/ingestion_timings.csv',list(ingestion[0]),ingestion)
        fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
        queue=[r['queue_wait_s'] for r in ingestion]; worker=[r['worker_s'] for r in ingestion]
        labels=[r['pdf_id'] for r in ingestion]
        ax.bar(labels,queue,label='Chờ worker',color='#E69F00',hatch='//')
        ax.bar(labels,worker,bottom=queue,label='Worker xử lý',color='#0072B2')
        ax.set(ylabel='Giây',title='Thời gian ingestion job — không gồm upload/validation trước enqueue');ax.legend()
        save(fig,'ingestion_timings')
    lines=['# Corpus cloud và kết quả hai PDF mới','',f"{len(inventory)} PDF, {sum(r['pages'] for r in inventory)} trang, {sum(r['chunk_count'] for r in inventory)} chunks active; embedding 384 chiều.",'',
           '| PDF | Nội dung | Lesson | Trang | Chunk | Ký tự | Trạng thái |','|---|---|---:|---:|---:|---:|---|']
    for r in inventory:lines.append(f"| {r['pdf_id']} | {r['title']} | {r['lesson_id']} | {r['pages']} | {r['chunk_count']} | {r['extracted_chars']} | {r['status']} |")
    lines+=['','![Corpus](corpus_profile.png)','', '## Hai PDF mới','',
            '| PDF | Yêu cầu | Lỗi | TB (s) | Median (s) | P95 (s) | Chồng lấp trang | Accuracy sơ bộ |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in fresh:
        fmt=lambda v:'Chờ chấm' if v is None else f'{v:.4f}'
        lines.append(f"| {r['source_id']} | {r['requests']} | {r['errors']} | {fmt(r['mean_s'])} | {fmt(r['median_s'])} | {fmt(r['p95_s'])} | {fmt(r['expected_page_overlap_proxy'])} | {fmt(r['strict_accuracy'])} |")
    lines+=['','![Hai PDF mới](new_pdfs_metrics.png)','',
            'Accuracy nếu có là điểm Codex đối chiếu thủ công với PDF/rubric, chỉ mang tính sơ bộ; không phải đánh giá độc lập của giảng viên. Proxy chồng lấp trang có thể thấp dù trả lời đúng khi nội dung được lặp ở trang khác, hoặc cao dù câu trả lời sai khi chunk chỉ chứa một phần của trang.', '',
            'Các bài học đã được tạo và index trong cloud ở trạng thái nháp, không preview. Giảng viên mở khóa học Demo AI Tutor với RAG trong trang quản lý tài liệu để xem/sử dụng; việc publish cho học viên cần kiểm tra riêng.', '',
            'Node.js dùng số trang vật lý của PDF: trang vật lý 8 tương ứng trang in 7. Router Express có các đoạn hội thoại và ví dụ kiểm tra admin bằng query parameter; bộ test chỉ hỏi cấu trúc/router, không dùng ví dụ đó làm chuẩn thiết kế bảo mật.', '',
            'Không đổi retrieval threshold/model/chunking trong đợt đo. Không chỉnh câu hỏi sau khi xem phản hồi; dataset/checksum gốc được giữ trong provenance và results.json.']
    if ingestion:
        lines+=['','## Thời gian ingestion job','', '| PDF | Attempts | Chờ worker (s) | Worker (s) | Tổng job (s) |','|---|---:|---:|---:|---:|']
        for row in ingestion:
            lines.append(f"| {row['pdf_id']} | {row['attempts']} | {row['queue_wait_s']:.3f} | {row['worker_s']:.3f} | {row['job_total_s']:.3f} |")
        lines+=['','![Ingestion](ingestion_timings.png)','', 'Thời gian job lấy trực tiếp từ created_at/started_at/completed_at trong cloud. Tổng job gồm chờ hàng đợi và worker; không tính thời gian kiểm tra PDF/upload storage trước khi tạo job.']
    (out/'CORPUS_AND_NEW_PDFS.md').write_text('\n'.join(lines),encoding='utf-8')
    for p in out.rglob('*'):
        if p.is_file():p.chmod(0o600)


if __name__=='__main__':main()
