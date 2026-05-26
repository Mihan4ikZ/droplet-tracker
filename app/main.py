from cli import parse_args
from process_data import process_video

def main():
    args = parse_args()
    process_video(
        input_video=args.input_video,
        output_video=args.output_video,
        output_csv=args.output_csv,
        position_threshold=args.position_threshold,
        area_ratio=args.area_ratio,
        dim_ratio=args.dim_ratio
    )

if __name__ == '__main__':
    main()