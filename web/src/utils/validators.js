/**
 * 格式验证工具函数
 */

/**
 * 验证镜像地址格式
 * @param {string} address 镜像地址
 * @returns {boolean} 是否有效
 */
export function validateImageAddress(address) {
  if (!address || typeof address !== 'string') {
    return false;
  }

  // 检查是否包含空格
  if (address.includes(' ')) {
    return false;
  }

  // 检查基本格式，应该是 docker://registry/image:tag 或 registry/image:tag
  const dockerPattern = /^docker:\/\/[a-zA-Z0-9._-]+(:[0-9]+)?\/[a-zA-Z0-9._-]+\/[a-zA-Z0-9._-]+(:[a-zA-Z0-9._-]+)?$/;
  const registryPattern = /^[a-zA-Z0-9._-]+(:[0-9]+)?\/[a-zA-Z0-9._-]+\/[a-zA-Z0-9._-]+(:[a-zA-Z0-9._-]+)?$/;

  return dockerPattern.test(address) || registryPattern.test(address);
}

/**
 * 验证认证信息格式
 * @param {string} authInfo 认证信息，格式为 username:password
 * @returns {boolean} 是否有效
 */
export function validateAuthInfo(authInfo) {
  if (!authInfo || typeof authInfo !== 'string') {
    return false;
  }

  // 检查是否包含空格
  if (authInfo.includes(' ')) {
    return false;
  }

  // 检查格式是否为 username:password
  const authPattern = /^[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+$/;

  return authPattern.test(authInfo);
}

/**
 * 获取格式错误信息
 * @param {string} type 验证类型 ('image' 或 'auth')
 * @returns {string} 错误信息
 */
export function getFormatErrorMessage(type) {
  switch (type) {
    case 'image':
      return '镜像地址格式不正确，应为 docker://registry/image:tag 或 registry/image:tag，且不能包含空格';
    case 'auth':
      return '认证信息格式不正确，应为 username:password，且不能包含空格';
    default:
      return '格式不正确';
  }
}
