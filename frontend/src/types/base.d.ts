export interface BaseEntity {
    id: number;
    created_at: string;
    created_by: number;
    created_by_name: string;
    updated_at: string;
    updated_by: number;
    updated_by_name: string;
    is_deleted: boolean;
}

export interface BaseQuery {
    page: number;
    page_size: number;
}

export interface BaseResponseList {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    results: BaseEntity[];
}