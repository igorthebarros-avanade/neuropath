import axios from 'axios'
import apiUrl from '@/src/domain/constants/apiUrl'

const apiService = {
    async getAnswer(question){
        const res = await axios.post(apiUrl + 'ask', {question: question})
        return res.data
    },

    async getFeedback(exam, results){
        const res = await axios.post(apiUrl + `feedback/${exam}`, {results: results})
        return res.data
    },

    async getQuestions(examCode, yesNoQuestions, qualitativeQuestions){
        const res = await axios.get(apiUrl + `questions/${examCode}/${yesNoQuestions}/${qualitativeQuestions}`)
        return res.data
    }
}

export default apiService