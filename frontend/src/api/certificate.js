import request from './request'

export function getCertificates(params) {
  return request.get('/certificates', { params })
}

export function getCertificate(id) {
  return request.get(`/certificates/${id}`)
}

export function createCertificate(data) {
  return request.post('/certificates', data)
}

export function approveCertificate(id) {
  return request.post(`/certificates/${id}/approve`)
}

export function rejectCertificate(id, reason) {
  return request.post(`/certificates/${id}/reject`, { reason })
}

export function revokeCertificate(id) {
  return request.post(`/certificates/${id}/revoke`)
}

export function renewCertificate(id) {
  return request.post(`/certificates/${id}/renew`)
}

export function downloadCertificate(id) {
  return request.get(`/certificates/${id}/download`, { responseType: 'blob' })
}
