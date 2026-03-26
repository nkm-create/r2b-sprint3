import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryOptions,
  UseMutationOptions,
} from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { apiClient, ApiError } from './client';

/**
 * ページネーション付きレスポンスの型
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

/**
 * ページネーションパラメータの型
 */
export interface PaginationParams {
  page?: number;
  size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

/**
 * 一覧取得フック生成関数
 */
export function useListQuery<T>(
  queryKey: string[],
  endpoint: string,
  params?: PaginationParams & Record<string, unknown>,
  options?: Omit<
    UseQueryOptions<PaginatedResponse<T>, AxiosError<ApiError>>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<PaginatedResponse<T>, AxiosError<ApiError>>({
    queryKey: [...queryKey, params],
    queryFn: async () => {
      const response = await apiClient.get<PaginatedResponse<T>>(endpoint, {
        params,
      });
      return response.data;
    },
    ...options,
  });
}

/**
 * 単一アイテム取得フック生成関数
 */
export function useItemQuery<T>(
  queryKey: string[],
  endpoint: string,
  id: string | undefined,
  options?: Omit<
    UseQueryOptions<T, AxiosError<ApiError>>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<T, AxiosError<ApiError>>({
    queryKey: [...queryKey, id],
    queryFn: async () => {
      const response = await apiClient.get<T>(`${endpoint}/${id}`);
      return response.data;
    },
    enabled: !!id,
    ...options,
  });
}

/**
 * 作成ミューテーションフック生成関数
 */
export function useCreateMutation<TData, TVariables>(
  endpoint: string,
  queryKeyToInvalidate: string[],
  options?: Omit<
    UseMutationOptions<TData, AxiosError<ApiError>, TVariables>,
    'mutationFn'
  >
) {
  const queryClient = useQueryClient();

  return useMutation<TData, AxiosError<ApiError>, TVariables>({
    mutationFn: async (data) => {
      const response = await apiClient.post<TData>(endpoint, data);
      return response.data;
    },
    onSuccess: (...args) => {
      queryClient.invalidateQueries({ queryKey: queryKeyToInvalidate });
      options?.onSuccess?.(...args);
    },
    ...options,
  });
}

/**
 * 更新ミューテーションフック生成関数
 */
export function useUpdateMutation<TData, TVariables extends { id: string }>(
  endpoint: string,
  queryKeyToInvalidate: string[],
  options?: Omit<
    UseMutationOptions<TData, AxiosError<ApiError>, TVariables>,
    'mutationFn'
  >
) {
  const queryClient = useQueryClient();

  return useMutation<TData, AxiosError<ApiError>, TVariables>({
    mutationFn: async (data) => {
      const { id, ...rest } = data;
      const response = await apiClient.put<TData>(`${endpoint}/${id}`, rest);
      return response.data;
    },
    onSuccess: (...args) => {
      queryClient.invalidateQueries({ queryKey: queryKeyToInvalidate });
      options?.onSuccess?.(...args);
    },
    ...options,
  });
}

/**
 * 削除ミューテーションフック生成関数
 */
export function useDeleteMutation(
  endpoint: string,
  queryKeyToInvalidate: string[],
  options?: Omit<
    UseMutationOptions<void, AxiosError<ApiError>, string>,
    'mutationFn'
  >
) {
  const queryClient = useQueryClient();

  return useMutation<void, AxiosError<ApiError>, string>({
    mutationFn: async (id) => {
      await apiClient.delete(`${endpoint}/${id}`);
    },
    onSuccess: (...args) => {
      queryClient.invalidateQueries({ queryKey: queryKeyToInvalidate });
      options?.onSuccess?.(...args);
    },
    ...options,
  });
}
